import traceback
import json
from fastapi import APIRouter, File as FastAPIFile, UploadFile, Form, Request
from fastapi import HTTPException
from fastapi.responses import FileResponse
from typing import Annotated
from tortoise.expressions import Q

from src.controllers.functions._generic.fileutils import UploadFileRecord
from src.controllers.functions._generic.fileutils import upload_file_write_to_upload_folder
from src.controllers.functions._generic.fileutils import make_file_ref_from_plaintext
from src.controllers.functions._generic.fileutils import remove_file_from_upload_folder
from src.controllers.functions._generic.fileutils import resolve_uploaded_file_path
from src.controllers.functions._generic.queryutils import render_debug_sql
from src.controllers.functions.file.file import create_entry_file
from src.controllers.functions.file.file import on_update_file
from src.controllers.functions.file.file import on_remove_file
from src.controllers.functions.file.file import fetch_es_docs
from src.controllers.functions.file_ingest import FILE_STATUS_INDEXED
from src.controllers.functions.file_ingest import FILE_STATUS_UPLOADING
from src.controllers.functions.file_ingest import FILE_STATUS_UPLOADED
from src.controllers.functions.file_ingest import create_file_process_log
from src.controllers.functions.file_ingest import enqueue_file_ingest
from src.controllers.functions.file_ingest import is_pdf_file
from src.controllers.functions.file_ingest import serialize_file_index_job
from src.controllers.functions.file_ingest import update_file_status
from src.controllers.functions.file_ingest import serialize_file_process_log
from src.controllers.functions.user.userauth_session import fetch_loggedin_user_info
from src.controllers.functions.user.userscope import user_has_permission
from src.controllers.functions.user.userscope import resolve_target_party_id
from src.controllers.functions.user.permissions import PermissionCode

from src.models.master import File, FileIndexJob, KMFile
from src.models.master import FileProcessLog
from src.models.master import Category, KMCategory

router = APIRouter(prefix="/api/v1")


TAG_C001 = "C_FILE001"
TAG_E001 = "E_FILE001"


async def _accessible_category_ids(user) -> list[str]:
  if user.role is None:
    return []
  await user.role.fetch_related("accessible_categorys")
  return [
    str(item.id)
    for item in user.role.accessible_categorys
    if not item.is_disabled and not item.is_deleted
  ]


def _ensure_file_manager(user):
  if not user_has_permission(user, PermissionCode.FILE_MANAGE):
    raise HTTPException(status_code=403, detail="Permission denied")

@router.post("/file/upload")
async def upload_and_create(
  request: Request,
  category_id: Annotated[str, Form()] = None,
  document_tags: Annotated[str, Form()] = None,
  document_title: Annotated[str, Form()] = None,
  document_summary: Annotated[str, Form()] = None,
  document_remarks: Annotated[str, Form()] = None,
  document_userdata: Annotated[str, Form()] = None,
  alias: Annotated[str, Form()] = None,
  file: UploadFile = FastAPIFile(),
  plaintext: Annotated[str, Form()] = None,
):
  try:
    headers = request.headers
    user, access_token = await fetch_loggedin_user_info(headers=headers)
    _ensure_file_manager(user)

    party_id = user.party_id

    if category_id not in [None, ""]:
      category = await Category.filter(
        id=category_id,
        party_id=party_id,
        is_disabled=False,
        is_deleted=False,
      ).first()
      if category is None:
        raise HTTPException(status_code=400, detail="Category not found")

    if (document_tags is not None):
      document_tags = [ tag.strip() for tag in document_tags.split(",") ]
      
    if (document_userdata is not None):
      document_userdata = json.loads(document_userdata)
    
    if plaintext is not None:
      return await upload_and_create_file_from_plaintext(
        party_id = party_id,
        category_id = category_id,
        document_tags = document_tags,
        document_title = document_title,
        document_summary = document_summary,
        document_remarks = document_remarks,
        document_userdata = document_userdata,
        alias = alias,
        plaintext = plaintext,
      )
      
    return await upload_and_create_file_from_file(
      party_id = party_id,
      category_id = category_id,
      document_tags = document_tags,
      document_title = document_title,
      document_summary = document_summary,
      document_remarks = document_remarks,
      document_userdata = document_userdata,
      alias = alias,
      file = file,
      requested_by_user_id = user.id,
    )

  except HTTPException:
    raise
  except Exception as e:
    stacktrace = traceback.format_exc()
    raise HTTPException(
      status_code=500,
      detail={
        "message": TAG_E001,
        "error": str(e),
        "stacktrace": stacktrace,
      }
    )



async def upload_and_create_file_from_file(
  party_id: str = None,
  category_id: str = None,
  document_tags: list[str] = None,
  document_title: str = None,
  document_summary: str = None,
  document_remarks: str = None,
  document_userdata = None,
  alias: str = None,
  file: UploadFile = FastAPIFile(),
  requested_by_user_id: str = None,
):
  try:
    file_ref, filebytes = await upload_file_write_to_upload_folder(
      file=file,
      alias=alias,
    )
    
    item = await create_entry_file(
      uploadFileRecord = file_ref,
      party_id=party_id,
      category_id=category_id,
      status=FILE_STATUS_UPLOADING,
      latest_process_message="Saving uploaded file",
      document_tags=document_tags,
      document_title=document_title,
      document_summary=document_summary,
      document_remarks=document_remarks,
      document_userdata=document_userdata,
    )

    await create_file_process_log(
      item,
      stage="UPLOAD",
      status="SUCCESS",
      message="File saved to upload storage",
      details_json={
        "filename": file_ref.filename,
        "size_bytes": file_ref.filesize,
      },
    )

    if is_pdf_file(item):
      await enqueue_file_ingest(item.id, requested_by_user_id=requested_by_user_id)
    else:
      await update_file_status(
        item,
        FILE_STATUS_UPLOADED,
        latest_process_message="Stored but not indexed; PDF files only",
        clear_ingest_error=True,
      )
      await create_file_process_log(
        item,
        stage="INDEXING",
        status="NOT_INDEXED",
        message="Stored but not indexed; PDF files only",
      )

    return {
      "success": True,
      "message": TAG_C001,
      "data": {
        "item": item,
      },
    }

  except Exception as e:
    raise e




async def upload_and_create_file_from_plaintext(
  party_id: str = None,
  category_id: str = None,
  document_tags: list[str] = None,
  document_title: str = None,
  document_summary: str = None,
  document_remarks: str = None,
  document_userdata = None,
  alias: str = None,
  plaintext: str = None,
):
  try:
    file_ref, filebytes = await make_file_ref_from_plaintext(
      plaintext=plaintext,
      alias=alias,
    )
    
    item = await create_entry_file(
      uploadFileRecord = file_ref,
      party_id=party_id,
      category_id=category_id,
      status=FILE_STATUS_UPLOADING,
      latest_process_message="Saving plaintext upload",
      document_tags=document_tags,
      document_title=document_title,
      document_summary=document_summary,
      document_remarks=document_remarks,
      document_userdata=document_userdata,
    )

    await create_file_process_log(
      item,
      stage="UPLOAD",
      status="SUCCESS",
      message="Plaintext saved to upload storage",
      details_json={
        "filename": file_ref.filename,
        "size_bytes": file_ref.filesize,
      },
    )

    await update_file_status(
      item,
      FILE_STATUS_UPLOADED,
      latest_process_message="Stored but not indexed; PDF files only",
      clear_ingest_error=True,
    )
    await create_file_process_log(
      item,
      stage="INDEXING",
      status="NOT_INDEXED",
      message="Stored but not indexed; PDF files only",
    )

    return {
      "success": True,
      "message": TAG_C001,
      "data": {
        "item": item,
      },
    }

  except Exception as e:
    raise e





@router.get("/file")
async def fetch(
  request: Request,
  page: int = 0,
  limit: int = 10,
  category_id: str = None,
  index_status: str = None,
):
  try:
    headers = request.headers
    user, access_token = await fetch_loggedin_user_info(headers=headers)
    
    # Calculate the offset based on the page and limit
    offset = (page) * limit
    
    # Fetch the category items from the database using Tortoise ORM
    filters = {}
    
    if category_id != "__ALL__":
      if (category_id == None):
        filters["category_id__isnull"] = True
      else:
        filters["category_id"] = category_id

    filters["party_id"] = user.party_id if user != None else None
    filters["is_disabled"] = False
    filters["is_deleted"] = False
    if not user_has_permission(user, PermissionCode.FILE_MANAGE):
      filters["category_id__in"] = await _accessible_category_ids(user)
    if index_status not in [None, ""]:
      filters["index_status"] = index_status

    items = (
      await File
        .filter(Q(**filters))
        .offset(offset)
        .limit(limit)
    )

    total_count = (
      await File
        .filter(Q(**filters))
        .count()
    )

    tsql = render_debug_sql(File.filter(Q(**filters)))

    return {
      "success": True,
      "message": TAG_C001,
      "data": {
        "filters": filters,
        "sql": tsql,
        "pagination": {
          "page": page,
          "limit": limit,
          "total_count": total_count,
        },
        "items": items,
      },
    }
  except HTTPException:
    raise
  except Exception as e:
    stacktrace = traceback.format_exc()
    raise HTTPException(
      status_code=500,
      detail={
        "message": TAG_E001,
        "error": str(e),
        "stacktrace": stacktrace,
      }
    )


@router.post("/file/index-jobs")
async def create_file_index_jobs(request: Request):
  try:
    user, access_token = await fetch_loggedin_user_info(headers=request.headers)
    if not user_has_permission(user, PermissionCode.FILE_INDEX):
      raise HTTPException(status_code=403, detail="Permission denied")

    data = await request.json()
    file_ids = list(dict.fromkeys(str(item) for item in (data.get("file_ids") or [])))
    if not file_ids:
      raise HTTPException(status_code=400, detail="file_ids is required")
    if len(file_ids) > 100:
      raise HTTPException(status_code=400, detail="At most 100 files can be queued at once")

    files = await File.filter(
      id__in=file_ids,
      party_id=user.party_id,
      is_disabled=False,
      is_deleted=False,
    )
    files_by_id = {str(item.id): item for item in files}
    results = []

    for file_id in file_ids:
      item = files_by_id.get(file_id)
      if item is None:
        results.append({"file_id": file_id, "queued": False, "error": "File not found"})
        continue
      try:
        job = await enqueue_file_ingest(item.id, requested_by_user_id=user.id)
        results.append({
          "file_id": file_id,
          "queued": True,
          "job": await serialize_file_index_job(job),
        })
      except ValueError as error:
        results.append({"file_id": file_id, "queued": False, "error": str(error)})

    return {
      "success": True,
      "message": TAG_C001,
      "data": {"results": results},
    }
  except HTTPException:
    raise
  except Exception as error:
    raise HTTPException(status_code=500, detail={
      "message": TAG_E001,
      "error": str(error),
      "stacktrace": traceback.format_exc(),
    })


@router.get("/file/index-jobs")
async def fetch_file_index_jobs(
  request: Request,
  page: int = 0,
  limit: int = 50,
  file_id: str = None,
  status: str = None,
):
  try:
    user, access_token = await fetch_loggedin_user_info(headers=request.headers)
    if not user_has_permission(user, PermissionCode.FILE_INDEX):
      raise HTTPException(status_code=403, detail="Permission denied")

    filters = {"party_id": user.party_id}
    if file_id not in [None, ""]:
      filters["file_id"] = file_id
    if status not in [None, ""]:
      filters["status"] = status

    query = FileIndexJob.filter(**filters)
    total_count = await query.count()
    items = await query.order_by("-created_at").offset(page * limit).limit(limit)
    return {
      "success": True,
      "message": TAG_C001,
      "data": {
        "pagination": {"page": page, "limit": limit, "total_count": total_count},
        "items": [await serialize_file_index_job(item) for item in items],
      },
    }
  except HTTPException:
    raise
  except Exception as error:
    raise HTTPException(status_code=500, detail={
      "message": TAG_E001,
      "error": str(error),
      "stacktrace": traceback.format_exc(),
    })




@router.get("/file/single")
async def fetchSingle(
  request: Request,
  id: str,
  party_id: str = None,
  is_fetch_es_docs: int = 0,
  is_fetch_process_logs: int = 0,
):
  try:
    headers = request.headers
    user, access_token = await fetch_loggedin_user_info(headers=headers)
    
    filters = {}
    filters["id"] = id
    filters["party_id"] = resolve_target_party_id(user, party_id)
    filters["is_disabled"] = False
    filters["is_deleted"] = False
    if not user_has_permission(user, PermissionCode.FILE_MANAGE):
      filters["category_id__in"] = await _accessible_category_ids(user)

    item = (
      await File
        .filter(Q(**filters))
        .prefetch_related()
        .first()
    )


    es_docs = []
    process_logs = []
    if (item != None):
      if (is_fetch_es_docs == 1):
        es_docs = await fetch_es_docs(
          party_id=item.party_id,
          file=item,
        )
      if (is_fetch_process_logs == 1):
        process_logs_raw = await FileProcessLog.filter(file_id=item.id).order_by("-created_at")
        process_logs = [await serialize_file_process_log(log_item) for log_item in process_logs_raw]
    

    return {
      "success": True,
      "message": TAG_C001,
      "data": {
        "item": item,
        "es_docs": es_docs,
        "process_logs": process_logs,
      },
    }

  except HTTPException:
    raise
  except Exception as e:
    stacktrace = traceback.format_exc()
    raise HTTPException(
      status_code=500,
      detail={
        "message": TAG_E001,
        "error": str(e),
        "stacktrace": stacktrace,
      }
    )


@router.get("/file/content")
async def fetch_file_content(request: Request, id: str):
  user, access_token = await fetch_loggedin_user_info(headers=request.headers)
  filters = {
    "id": id,
    "party_id": user.party_id,
    "is_disabled": False,
    "is_deleted": False,
  }
  if not user_has_permission(user, PermissionCode.FILE_MANAGE):
    filters["category_id__in"] = await _accessible_category_ids(user)
  item = await File.filter(**filters).first()
  if item is None:
    raise HTTPException(status_code=404, detail="File not found")
  return FileResponse(
    resolve_uploaded_file_path(item.filename),
    media_type=item.mime_type or "application/octet-stream",
    filename=item.alias or item.filename,
    content_disposition_type="inline",
  )


@router.delete("/file")
async def remove(
  request: Request,
  id: str,
):
  try:
    headers = request.headers
    user, access_token = await fetch_loggedin_user_info(headers=headers)
    _ensure_file_manager(user)

    filters = {}
    filters["party_id"] = user.party_id if user != None else None
    filters["id"] = id

    item = (
      await File
        .filter(Q(**filters))
        .first()
    )
    
    if not item:
      raise HTTPException(status_code=404, detail="File not found")

    await on_remove_file(
      party_id=user.party_id,
      file=item,
    )

    item.is_deleted = True
    await item.save()

    await create_file_process_log(
      item,
      stage="DELETE",
      status="SUCCESS",
      message="File deleted",
    )
    
    is_file_deleted = await remove_file_from_upload_folder(
      filename=item.filename,
    )
    
    return {
      "success": True,
      "message": TAG_C001,
      "data": {
        "item": item,
        "is_file_deleted": is_file_deleted,
      },
    }
    
    
  except HTTPException:
    raise
  except Exception as e:
    stacktrace = traceback.format_exc()
    raise HTTPException(
      status_code=500,
      detail={
        "message": TAG_E001,
        "error": str(e),
        "stacktrace": stacktrace,
      }
    )
    


@router.patch("/file")
async def update(
  request: Request,
  id: str,
):
  try:
    headers = request.headers
    user, access_token = await fetch_loggedin_user_info(headers=headers)
    _ensure_file_manager(user)

    filters = {}
    filters["party_id"] = user.party_id if user != None else None
    filters["id"] = id

    item = (
      await File
        .filter(Q(**filters))
        .first()
    )
    
    if not item:
      raise HTTPException(status_code=404, detail="File not found")

    data = await request.json()


    if "category_id" in data:
      if data["category_id"] not in [None, ""]:
        category = await Category.filter(
          id=data["category_id"],
          party_id=user.party_id,
          is_disabled=False,
          is_deleted=False,
        ).first()
        if category is None:
          raise HTTPException(status_code=400, detail="Category not found")
      item.category_id = data["category_id"]
      if item.status == FILE_STATUS_INDEXED:
        await on_update_file(
          party_id=user.party_id,
          file=item,
          category_id=item.category_id
        )

    if "alias" in data:
      item.alias = data["alias"]


    await item.save()
    
    
    
    return {
      "success": True,
      "message": TAG_C001,
      "data": {
        "item": item,
      },
    }
    
    
  except HTTPException:
    raise
  except Exception as e:
    stacktrace = traceback.format_exc()
    raise HTTPException(
      status_code=500,
      detail={
        "message": TAG_E001,
        "error": str(e),
        "stacktrace": stacktrace,
      }
    )
    
