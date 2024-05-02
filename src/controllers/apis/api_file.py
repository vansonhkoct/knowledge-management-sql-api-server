import traceback
from fastapi import APIRouter, File, UploadFile, Form, Request
from fastapi import HTTPException
from typing import Annotated
from tortoise.expressions import Q

import sys
import os

parent_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(parent_dir + "/../../")

from controllers.functions._generic.fileutils import UploadFileRecord, upload_file_write_to_upload_folder
from controllers.functions.file.file import create_entry_file

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
  file: UploadFile = File(),
):
  try:
    headers = request.headers
  
    # Save the uploaded file to the local "./upload" folder
    file_ref = await upload_file_write_to_upload_folder(
      file=file,
      alias=alias,
    )
    
    item = await create_entry_file(
      uploadFileRecord = file_ref,
      category_id=category_id,
    )
    
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
    
    # Calculate the offset based on the page and limit
    offset = (page) * limit
    
    # Fetch the category items from the database using Tortoise ORM
    filters = {}
    
    if category_id != "__ALL__":
      if (category_id == None):
        filters["category_id__isnull"] = True
      else:
        filters["category_id"] = category_id

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
):
  try:
    headers = request.headers
    
    filters = {}
    filters["id"] = id
    filters["is_disabled"] = False
    filters["is_deleted"] = False

    item = (
      await File
        .filter(Q(**filters))
        .first()
    )
    

    return {
      "success": True,
      "message": TAG_C001,
      "data": item,
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
  
    item = await File.filter(id=id).first()
    
    if not item:
      raise HTTPException(status_code=404, detail="File not found")


    item.is_deleted = True
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
    


@router.patch("/file")
async def update(
  request: Request,
  id: str,
):
  try:
    headers = request.headers
  
    item = await File.filter(id=id).first()
    if not item:
      raise HTTPException(status_code=404, detail="File not found")

    
    
    data = await request.json()


    if "category_id" in data:
      item.category_id = data["category_id"]

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
    




# @router.post("/file")
# async def move(
#   request: Request,
#   category_id: Annotated[str, Form()] = None,
#   # file: UploadFile = File(...),
#   file: UploadFile = File(),
# ):
#     headers = request.headers
  
#     # Save the uploaded file to the local "./upload" folder
#     file_ref = await upload_file_write_to_upload_folder(
#       file=file,
#     )
    
#     file_entry = await create_entry_file(
#       uploadFileRecord = file_ref,
#     )
    
#     return {
#       "success": True,
#       "message": TAG_C001,
#       "data": {
#         "item": file_entry,
#         "c": category_id,
#       },
#     }

