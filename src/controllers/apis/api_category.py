import traceback
from fastapi import APIRouter, File, UploadFile, Form, Request
from fastapi import HTTPException
from typing import Annotated
from tortoise.expressions import Q

import sys
import os

parent_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(parent_dir + "/../../")

from controllers.functions._generic.modelutils import makeObjectID
from tortoise.exceptions import IntegrityError
from tortoise.contrib.fastapi import HTTPNotFoundError

router = APIRouter(prefix="/api/v1")



from models.master import Category, KMCategory


TAG_C001 = "C_CATEGORY001"
TAG_E001 = "E_CATEGORY001"


@router.get("/category")
async def fetch(
  request: Request,
  page: int = 0,
  limit: int = 10,
  parent_category_id: str = None,
):
  try:
    headers = request.headers
    
    # Calculate the offset based on the page and limit
    offset = (page) * limit
    
    # Fetch the category items from the database using Tortoise ORM
    filters = {}
    
    if parent_category_id != "__ALL__":
      if (parent_category_id == None):
        filters["parent_category_id__isnull"] = True
      else:
        filters["parent_category_id"] = parent_category_id

    filters["is_disabled"] = False
    filters["is_deleted"] = False

    items = (
      await Category
        .filter(Q(**filters))
        .offset(offset)
        .limit(limit)
    )
    
    total_count = (
      await Category
        .filter(Q(**filters))
        .count()
    )

    tsql = (
      Category
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




@router.get("/category/single")
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
      await Category
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






@router.post("/category")
async def create(
  request: Request,
):
  try:
    headers = request.headers
    data = await request.json()
    
    payload = {}
    
    if "parent_category_id" in data:
      payload["parent_category_id"] = data["parent_category_id"]

    if "alias" in data:
      payload["alias"] = data["alias"]
      payload["folderpath_absolute"] = None


    item = await Category.create(**payload)

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


@router.delete("/category")
async def remove(
  request: Request,
  id: str,
):
  try:
    headers = request.headers
  
    item = await Category.filter(id=id).first()
    
    if not item:
      raise HTTPException(status_code=404, detail="Category not found")


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
    


@router.patch("/category")
async def update(
  request: Request,
  id: str,
):
  try:
    headers = request.headers
  
    item = await Category.filter(id=id).first()
    if not item:
      raise HTTPException(status_code=404, detail="Category not found")

    
    
    data = await request.json()


    if "parent_category_id" in data:
      item.parent_category_id = data["parent_category_id"]

    if "alias" in data:
      item.alias = data["alias"]
      item.folderpath_absolute = None


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
    




# @router.post("/category")
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

