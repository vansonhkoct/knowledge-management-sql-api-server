import traceback
from fastapi import APIRouter, File, UploadFile, Form, Request
from fastapi import HTTPException
from typing import Annotated
from tortoise.expressions import Q
from itertools import groupby

from tortoise.exceptions import IntegrityError
from tortoise.contrib.fastapi import HTTPNotFoundError

from src.controllers.functions._generic.modelutils import makeObjectID
from src.controllers.functions.user.userauth_session import fetch_loggedin_user_info
from src.controllers.functions._generic.queryutils import fetch_paginated, fetch_single, wrapped_api_task

from src.models.master import Permission
from src.models.master import Role


router = APIRouter(prefix="/api/v1")


TAG_C001 = "C_ROLE_PERMISSION001"
TAG_E001 = "E_ROLE_PERMISSION001"







@router.get("/role_permissions/role_permissions")
async def fetch_role_permissions(
  request: Request,
  page: int = 0,
  limit: int = 10,
  party_id: str = None
):
  async def asyncjob(
    headers, user, access_token,
  ):
    # Calculate the offset based on the page and limit
    offset = (page) * limit
    
    # Fetch the permission items from the database using Tortoise ORM
    filters = {}
    filters["party_id"] = (user.party_id if user != None else None)
    filters["roles__id"] = (party_id if party_id != None else user.party_id if user != None else None)
    filters["roles__is_disabled"] = False
    filters["roles__is_deleted"] = False
    filters["is_disabled"] = False
    filters["is_deleted"] = False

    items, total_count, tsql = await fetch_paginated(
      model=Permission,
      filters=filters,
      offset=offset,
      limit=limit,
    )
    
    return {
      "filters": filters,
      "sql": tsql,
      "pagination": {
        "page": page,
        "limit": limit,
        "total_count": total_count,
      },
      "items": items,
    }
  
  return await wrapped_api_task(
    request=request,
    fetch_loggedin_user_info=fetch_loggedin_user_info,
    asyncjob=asyncjob,
    code_success=TAG_C001,
    code_error=TAG_E001,
  )
  


@router.get("/role_permissions/permission_roles")
async def fetch_permission_roles(
  request: Request,
  page: int = 0,
  limit: int = 10,
  permission_id: str = None
):
  async def asyncjob(
    headers, user, access_token,
  ):
    # Calculate the offset based on the page and limit
    offset = (page) * limit
    
    # Fetch the permission items from the database using Tortoise ORM
    filters = {}
    filters["party_id"] = (user.party_id if user != None else None)
    filters["permissions__id"] = (permission_id if permission_id != None else None)
    filters["permissions__is_disabled"] = False
    filters["permissions__is_deleted"] = False
    filters["is_disabled"] = False
    filters["is_deleted"] = False

    items, total_count, tsql = await fetch_paginated(
      model=Role,
      filters=filters,
      offset=offset,
      limit=limit,
    )
    
    return {
      "filters": filters,
      "sql": tsql,
      "pagination": {
        "page": page,
        "limit": limit,
        "total_count": total_count,
      },
      "items": items,
    }
  
  return await wrapped_api_task(
    request=request,
    fetch_loggedin_user_info=fetch_loggedin_user_info,
    asyncjob=asyncjob,
    code_success=TAG_C001,
    code_error=TAG_E001,
  )
  




@router.post("/role_permissions/bulk_update")
async def bulk_update_mappings(
  request: Request,
):
  try:
    headers = request.headers
    user, access_token = await fetch_loggedin_user_info(headers=headers)


    map_key_x = "permission_id"
    map_key_y = "role_id"


    data = await request.json()
    add_mappings = data["add_mappings"] if "add_mappings" in data else []
    remove_mappings = data["remove_mappings"] if "remove_mappings" in data else []



    # TODO: bulk add
    for dict in add_mappings:
      permission = await Permission.filter( Q(**{ "id": dict[map_key_x] }) ).first()
      role = await Role.filter( Q(**{ "id": dict[map_key_y] }) ).first()
      if (permission != None and role != None):
        await permission.roles.add(role)


    # TODO: bulk remove
    for dict in remove_mappings:
      permission = await Permission.filter( Q(**{ "id": dict[map_key_x] }) ).first()
      role = await Role.filter( Q(**{ "id": dict[map_key_y] }) ).first()
      if (permission != None and role != None):
        await permission.roles.remove(role)


    return {
      "success": True,
      "message": TAG_C001,
      "data": {
        "add_mappings": add_mappings,
        "remove_mappings": remove_mappings,
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




