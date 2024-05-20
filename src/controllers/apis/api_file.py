import traceback
from fastapi import APIRouter, File as FastAPIFile, UploadFile, Form, Request
from fastapi import HTTPException
from typing import Annotated
from tortoise.expressions import Q

import sys
import os

parent_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(parent_dir + "/../../")

from controllers.functions._generic.fileutils import UploadFileRecord
from controllers.functions._generic.fileutils import upload_file_write_to_upload_folder
from controllers.functions._generic.fileutils import remove_file_from_upload_folder
from controllers.functions.file.file import create_entry_file
from controllers.functions.file.file import on_move_file
from controllers.functions.file.file import on_remove_file
from controllers.functions.file.file import on_upload_file
from controllers.functions.file.file import fetch_es_docs
from controllers.functions.user.userauth_session import fetch_loggedin_user_info

router = APIRouter(prefix="/api/v1")

from models.master import File, KMFile
from models.master import Category, KMCategory


TAG_C001 = "C_FILE001"
TAG_E001 = "E_FILE001"


@router.post("/file/upload")
async def upload_and_create(
  request: Request,
  category_id: Annotated[str, Form()] = None,
  alias: Annotated[str, Form()] = None,
  # file: UploadFile = File(...),
  file: UploadFile = FastAPIFile(),
):
  try:
    headers = request.headers
    user, access_token = await fetch_loggedin_user_info(headers=headers)
    # Save the uploaded file to the local "./upload" folder
    file_ref, filebytes = await upload_file_write_to_upload_folder(
      file=file,
      alias=alias,
    )
    
    item = await create_entry_file(
      uploadFileRecord = file_ref,
      party_id=user.party_id,
      category_id=category_id,
    )
    
    es_doc_ids = []
    
    with open(file_ref.filepath, "rb") as r_file:
      docs, es_doc_ids = await on_upload_file(
        party_id=user.party_id,
        filename=file_ref.filename,
        file_id=item.id,
        file=r_file,
        category_id=category_id,
      )
    
    item.es_doc_ids = ",".join(es_doc_ids if es_doc_ids != None else [])
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
  is_fetch_es_docs: int = 0,
):
  try:
    headers = request.headers
    user, access_token = await fetch_loggedin_user_info(headers=headers)
    
    filters = {}
    filters["id"] = id
    filters["party_id"] = user.party_id if user != None else None
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
      
      await on_move_file(
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
    

