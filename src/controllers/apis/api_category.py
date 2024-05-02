import traceback
from fastapi import APIRouter, File, UploadFile, Form, Request
from typing import Annotated
from tortoise.expressions import Q

import sys
import os

parent_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(parent_dir + "/../../")

from controllers.functions._generic.fileutils import folder_create
from controllers.functions._generic.modelutils import makeObjectID
from tortoise.exceptions import IntegrityError

router = APIRouter(prefix="/api/v1")



from models.master import Category, KMCategory



@router.get("/category")
async def fetch(
  request: Request,
  page: int = 0,
  limit: int = 10,
  parent_category_id: int = None,
):
    headers = request.headers
    
    # Calculate the offset based on the page and limit
    offset = (page) * limit
    
    # Fetch the category items from the database using Tortoise ORM
    filters = {}
    if parent_category_id is not None:
      filters["parent_category_id"] = parent_category_id

    print(Q(**filters))

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


    return {
      "success": True,
      "message": "C_CAT001",
      "data": {
        "pagination": {
          "page": page,
          "limit": limit,
          "total_count": total_count,
        },
        "item": items,
      },
    }


@router.post("/category")
async def create(
  request: Request,
):
    headers = request.headers
    data = await request.json()
    
    payload = {
      "name": data["name"] if "name" in data else "",
      "parent_category_id": data["parent_category_id"] if "parent_category_id" in data else None,
    }
    
    try:
      item = await Category.create(**payload)
  
      return {
        "success": True,
        "message": "C_F001",
        "data": {
          "item": item,
        },
      }
    except Exception as e:
      stacktrace = traceback.format_exc()
      return {
        "success": False,
        "message": "E_F001",
        "error": str(e),
        "stacktrace": stacktrace,
      }
      

# @router.delete("/category")
# async def remove(
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
#       "message": "C_F001",
#       "data": {
#         "item": file_entry,
#         "c": category_id,
#       },
#     }




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
#       "message": "C_F001",
#       "data": {
#         "item": file_entry,
#         "c": category_id,
#       },
#     }

