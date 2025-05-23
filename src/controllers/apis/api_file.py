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
from src.controllers.functions.file.file import on_upload_file
from src.controllers.functions.file.file import fetch_es_docs
from src.controllers.functions.user.userauth_session import fetch_loggedin_user_info

from src.models.master import File, KMFile
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
    # Save the uploaded file to the local "./upload" folder
    file_ref, filebytes = await upload_file_write_to_upload_folder(
      file=file,
      alias=alias,
    )
    
    item = await create_entry_file(
      uploadFileRecord = file_ref,
      party_id=party_id,
      category_id=category_id,
    )
    
    es_doc_ids = []
    
    
    with open(file_ref.filepath, "rb") as r_file:
      docs, es_doc_ids, index_name = await on_upload_file(
        party_id=party_id,
        filename=file_ref.filename,
        file_id=item.id,
        file=r_file,
        category_id=category_id,
        document_tags=document_tags,
        document_title=document_title,
        document_summary=document_summary,
        document_remarks=document_remarks,
        document_userdata=document_userdata,
      )
    
    
    item.es_doc_ids = ",".join(es_doc_ids if es_doc_ids is not None else [])
    await item.save()

    return {
      "success": True,
      "message": TAG_C001,
      "data": {
        "item": item,
        "es_doc_ids": es_doc_ids,
        "index_name": index_name,
        "docs": docs,
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
    # Obtain file_ref from plaintext
    file_ref, filebytes = await make_file_ref_from_plaintext(
      plaintext=plaintext,
      alias=alias,
    )
    
    item = await create_entry_file(
      uploadFileRecord = file_ref,
      party_id=party_id,
      category_id=category_id,
    )
    
    es_doc_ids = []
    
    docs, es_doc_ids, index_name = await on_upload_file(
      party_id=party_id,
      filename=file_ref.filename,
      file_id=item.id,
      plaintext=plaintext,
      category_id=category_id,
      document_tags=document_tags,
      document_title=document_title,
      document_summary=document_summary,
      document_remarks=document_remarks,
      document_userdata=document_userdata,
    )
    
    item.es_doc_ids = ",".join(es_doc_ids if es_doc_ids is not None else [])
    await item.save()

    return {
      "success": True,
      "message": TAG_C001,
      "data": {
        "item": item,
        "es_doc_ids": es_doc_ids,
        "index_name": index_name,
        "docs": docs,
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
    if (item != None):
      if (is_fetch_es_docs == 1):
        es_docs = await fetch_es_docs(
          party_id=item.party_id,
          file=item,
        )
    

    return {
      "success": True,
      "message": TAG_C001,
      "data": {
        "item": item,
        "es_docs": es_docs,
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

    await on_remove_file(
      party_id=user.party_id,
      file=item,
    )

    item.is_deleted = True
    await item.save()
    
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
    

