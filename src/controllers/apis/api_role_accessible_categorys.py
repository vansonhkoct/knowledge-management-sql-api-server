import traceback
from fastapi import APIRouter, File, UploadFile, Form, Request
from fastapi import HTTPException
from typing import Annotated
from tortoise.expressions import Q
from itertools import groupby

import sys
import os

parent_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(parent_dir + "/../../")

from controllers.functions._generic.modelutils import makeObjectID
from tortoise.exceptions import IntegrityError
from tortoise.contrib.fastapi import HTTPNotFoundError

router = APIRouter(prefix="/api/v1")



from models.master import Category, KMCategory
from models.master import Role
from controllers.functions.user.userauth_session import fetch_loggedin_user_info
from controllers.functions._generic.queryutils import fetch_paginated, fetch_single, wrapped_api_task



TAG_C001 = "C_ROLE_ACCESSIBLE_CATEGORY001"
TAG_E001 = "E_ROLE_ACCESSIBLE_CATEGORY001"







@router.get("/role_accessible_categorys/role_accessible_categorys")
async def fetch_role_accessible_categorys(
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
    
    # Fetch the category items from the database using Tortoise ORM
    filters = {}
    filters["party_id"] = (user.party_id if user != None else None)
    filters["accessible_roles__id"] = (party_id if party_id != None else user.party_id if user != None else None)
    filters["accessible_roles__is_disabled"] = False
    filters["accessible_roles__is_deleted"] = False
    filters["is_disabled"] = False
    filters["is_deleted"] = False
    filters["accessible_roles__permissions__code"] = "knowledge -> search"

    items, total_count, tsql = await fetch_paginated(
      model=Category,
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
  


@router.get("/role_accessible_categorys/category_accessible_roles")
async def fetch_category_accessible_roles(
  request: Request,
  page: int = 0,
  limit: int = 10,
  category_id: str = None
):
  async def asyncjob(
    headers, user, access_token,
  ):
    # Calculate the offset based on the page and limit
    offset = (page) * limit
    
    # Fetch the category items from the database using Tortoise ORM
    filters = {}
    filters["party_id"] = (user.party_id if user != None else None)
    filters["accessible_categorys__id"] = (category_id if category_id != None else None)
    filters["accessible_categorys__is_disabled"] = False
    filters["accessible_categorys__is_deleted"] = False
    filters["is_disabled"] = False
    filters["is_deleted"] = False
    filters["permissions__code"] = "knowledge -> search"

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
  




@router.post("/role_accessible_categorys/bulk_update")
async def bulk_update_mappings(
  request: Request,
):
  try:
    headers = request.headers
    user, access_token = await fetch_loggedin_user_info(headers=headers)


    map_key_x = "category_id"
    map_key_y = "role_id"


    data = await request.json()
    add_mappings = data["add_mappings"] if "add_mappings" in data else []
    remove_mappings = data["remove_mappings"] if "remove_mappings" in data else []



    # TODO: bulk add
    for dict in add_mappings:
      category = await Category.filter( Q(**{ "id": dict[map_key_x] }) ).first()
      role = await Role.filter( Q(**{ "id": dict[map_key_y] }) ).first()
      if (category != None and role != None):
        await role.accessible_categorys.add(category)


    # TODO: bulk remove
    for dict in remove_mappings:
      category = await Category.filter( Q(**{ "id": dict[map_key_x] }) ).first()
      role = await Role.filter( Q(**{ "id": dict[map_key_y] }) ).first()
      if (category != None and role != None):
        await role.accessible_categorys.remove(category)


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




