import traceback
import json
from fastapi import APIRouter, File as FastAPIFile, UploadFile, Form, Request
from fastapi import HTTPException
from typing import Annotated
from tortoise.expressions import Q

from src.controllers.functions._generic.fileutils import UploadFileRecord
from src.controllers.functions._generic.fileutils import upload_file_write_to_upload_folder
from src.controllers.functions._generic.fileutils import make_file_ref_from_plaintext
from src.controllers.functions._generic.fileutils import remove_file_from_upload_folder
from src.controllers.functions.file.file import bootstrapImportESBundle
from src.controllers.functions.file.file import create_entry_file
from src.controllers.functions.file.file import on_update_file
from src.controllers.functions.file.file import on_remove_file
from src.controllers.functions.file.file import fetch_es_docs
from src.controllers.functions.file_ingest import FILE_STATUS_ERROR
from src.controllers.functions.file_ingest import FILE_STATUS_INDEXED
from src.controllers.functions.file_ingest import FILE_STATUS_QUEUED
from src.controllers.functions.file_ingest import FILE_STATUS_UPLOADING
from src.controllers.functions.file_ingest import create_file_process_log
from src.controllers.functions.file_ingest import enqueue_file_ingest
from src.controllers.functions.file_ingest import update_file_status
from src.controllers.functions.file_ingest import serialize_file_process_log
from src.controllers.functions.user.userauth_session import fetch_loggedin_user_info

from src.models.master import File, KMFile
from src.models.master import FileProcessLog
from src.models.master import Category, KMCategory

router = APIRouter(prefix="/api/v1")


TAG_C001 = "C_FILE001"
TAG_E001 = "E_FILE001"

@router.post("/file/initializeES")
async def initializeES(
  request: Request,
):
  try:
    bootstrapImportESBundle()
    
    return {
      "success": True,
      "message": TAG_C001,
      "data": {
      },
    }

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

    party_id = user.party_id

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
    )

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

    try:
      await enqueue_file_ingest(item.id)
      await update_file_status(
        item,
        FILE_STATUS_QUEUED,
        latest_process_message="Queued for indexing",
        clear_ingest_error=True,
      )
      await create_file_process_log(
        item,
        stage="QUEUE",
        status="QUEUED",
        message="File queued for indexing",
      )
    except Exception as queue_error:
      stacktrace = traceback.format_exc()
      await update_file_status(
        item,
        FILE_STATUS_ERROR,
        latest_process_message=str(queue_error),
        ingest_error=stacktrace,
      )
      await create_file_process_log(
        item,
        stage="QUEUE",
        status="ERROR",
        message=str(queue_error),
        details_json={
          "stacktrace": stacktrace,
        },
      )
      raise queue_error

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

    try:
      await enqueue_file_ingest(item.id)
      await update_file_status(
        item,
        FILE_STATUS_QUEUED,
        latest_process_message="Queued for indexing",
        clear_ingest_error=True,
      )
      await create_file_process_log(
        item,
        stage="QUEUE",
        status="QUEUED",
        message="File queued for indexing",
      )
    except Exception as queue_error:
      stacktrace = traceback.format_exc()
      await update_file_status(
        item,
        FILE_STATUS_ERROR,
        latest_process_message=str(queue_error),
        ingest_error=stacktrace,
      )
      await create_file_process_log(
        item,
        stage="QUEUE",
        status="ERROR",
        message=str(queue_error),
        details_json={
          "stacktrace": stacktrace,
        },
      )
      raise queue_error

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

    tsql = (
      File
        .filter(Q(**filters))
        .sql()
    )

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
    filters["party_id"] = party_id if party_id != None else (user.party_id if user != None else None)
    filters["is_disabled"] = False
    filters["is_deleted"] = False

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





@router.delete("/file")
async def remove(
  request: Request,
  id: str,
):
  try:
    headers = request.headers
    user, access_token = await fetch_loggedin_user_info(headers=headers)

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

    if item.status == FILE_STATUS_INDEXED:
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
    

