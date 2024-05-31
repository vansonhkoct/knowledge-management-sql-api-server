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
from models.master import Party, PartyAccessibleSharedCategory
from controllers.functions.user.userauth_session import fetch_loggedin_user_info
from controllers.functions._generic.queryutils import fetch_paginated, fetch_single, wrapped_api_task



TAG_C001 = "C_PARTY_SHARED_CATEGORY001"
TAG_E001 = "E_PARTY_SHARED_CATEGORY001"







@router.get("/party_shared_categorys")
async def fetch_party_shared_categorys(
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
    filters["rel_PartyAccessibleSharedCategory__party__id"] = (party_id if party_id != None else user.party_id if user != None else None)
    filters["rel_PartyAccessibleSharedCategory__party__is_disabled"] = False
    filters["rel_PartyAccessibleSharedCategory__party__is_deleted"] = False
    filters["is_disabled"] = False
    filters["is_deleted"] = False

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
  


@router.get("/category_shared_partys")
async def fetch_category_shared_partys(
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
    filters["rel_PartyAccessibleSharedCategory__category__id"] = (category_id if category_id != None else None)
    filters["rel_PartyAccessibleSharedCategory__category__is_disabled"] = False
    filters["rel_PartyAccessibleSharedCategory__category__is_deleted"] = False
    filters["is_disabled"] = False
    filters["is_deleted"] = False

    items, total_count, tsql = await fetch_paginated(
      model=Party,
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
  




@router.post("/party_shared_categorys")
async def bulk_update_mappings(
  request: Request,
):
  try:
    headers = request.headers
    user, access_token = await fetch_loggedin_user_info(headers=headers)


    map_key_x = "category_id"
    map_key_y = "party_id"


    data = await request.json()
    add_mappings = data["add_mappings"] if "add_mappings" in data else []
    remove_mappings = data["remove_mappings"] if "remove_mappings" in data else []



    # bulk add
    add_records = [ (
      PartyAccessibleSharedCategory(**{
        map_key_x: dict[map_key_x],
        map_key_y: dict[map_key_y],
      })
    ) for dict in add_mappings ]

    if (len(add_records) > 0):
      await PartyAccessibleSharedCategory.bulk_create(add_records)



    # bulk remove
    grouped_remove_mappings = { key: list(it[map_key_y] for it in group) for key, group in groupby(remove_mappings, key=lambda x: x[map_key_x]) }

    for key, items in grouped_remove_mappings.items():
      
      filters = {}
      filters[map_key_x] = key
      filters[f"{map_key_y}__in"] = items
      
      if (len(items) > 0):
        print("deleting: " , filters , await PartyAccessibleSharedCategory.filter(Q(**filters)))
        await PartyAccessibleSharedCategory.filter(Q(**filters)).delete()


    return {
      "success": True,
      "message": TAG_C001,
      "data": {
        "user": user,
        "grouped_remove_mappings": grouped_remove_mappings,
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




