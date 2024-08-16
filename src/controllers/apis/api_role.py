import traceback
from fastapi import APIRouter, File, UploadFile, Form, Request
from fastapi import HTTPException
from typing import Annotated
from tortoise.expressions import Q

from src.controllers.functions._generic.fileutils import UploadFileRecord, upload_file_write_to_upload_folder
from src.controllers.functions.file.file import create_entry_file
from src.controllers.functions.user.userauth_session import fetch_loggedin_user_info

from src.models.master import User, Role, Permission


router = APIRouter(prefix="/api/v1")


TAG_C001 = "C_ROLE001"
TAG_E001 = "E_ROLE001"




@router.post("/role")
async def role_create(
  request: Request,
):
  try:
    headers = request.headers
    user, access_token = await fetch_loggedin_user_info(headers=headers)
    
    payload = {
      "party_id": user.party_id,
    }
    
    item = await Role.create(**payload)

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




@router.get("/role")
async def fetch(
  request: Request,
  page: int = 0,
  limit: int = 10,
  permission_code: str = None,
):
  try:
    headers = request.headers
    user, access_token = await fetch_loggedin_user_info(headers=headers)
    
    # Calculate the offset based on the page and limit
    offset = (page) * limit
    
    # Fetch the category items from the database using Tortoise ORM
    filters = {}
    
    filters["is_disabled"] = False
    filters["is_deleted"] = False
    filters["party_id"] = user.party_id
    if permission_code != None:
      filters["permissions__code"] = permission_code

    items = (
      await Role
        .filter(Q(**filters))
        .offset(offset)
        .limit(limit)
    )
    
    total_count = (
      await Role
        .filter(Q(**filters))
        .count()
    )

    tsql = (
      Role
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







@router.get("/role/single")
async def fetchSingle(
  request: Request,
  id: str,
):
  try:
    headers = request.headers
    user, access_token = await fetch_loggedin_user_info(headers=headers)
    
    filters = {}
    filters["id"] = id
    filters["is_disabled"] = False
    filters["is_deleted"] = False
    filters["party_id"] = user.party_id

    item = (
      await Role
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
