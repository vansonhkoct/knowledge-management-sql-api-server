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



from models.master import ChatMessage
from controllers.functions.user.userauth_session import fetch_loggedin_user_info
from controllers.functions._generic.queryutils import fetch_paginated, wrapped_api_task



TAG_C001 = "C_CHATMESSAGE001"
TAG_E001 = "E_CHATMESSAGE001"


@router.get("/chatmessage")
async def fetch(
  request: Request,
  page: int = 0,
  limit: int = 10,
  chat_id: str = None,
):
  async def asyncjob(
    request, headers, user, access_token,
  ):
    # Calculate the offset based on the page and limit
    offset = (page) * limit
    
    # Fetch the permission items from the database using Tortoise ORM
    filters = {}
    filters["chat_id"] = chat_id
    filters["is_disabled"] = False
    filters["is_deleted"] = False

    items, total_count, tsql = await fetch_paginated(
      model=ChatMessage,
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




@router.get("/chatmessage/single")
async def fetchSingle(
  request: Request,
  id: str,
  chat_id: str = None,
):
  async def asyncjob(
    request, headers, user, access_token,
  ):
    # Fetch the permission items from the database using Tortoise ORM
    filters = {}
    filters["chat_id"] = chat_id
    filters["id"] = id
    filters["is_disabled"] = False
    filters["is_deleted"] = False

    item = (
      await ChatMessage
        .filter(Q(**filters))
        .first()
    )

    return item
  
  return await wrapped_api_task(
    request=request,
    fetch_loggedin_user_info=fetch_loggedin_user_info,
    asyncjob=asyncjob,
    code_success=TAG_C001,
    code_error=TAG_E001,
  )
  





@router.post("/chatmessage")
async def create(
  request: Request,
):
  async def asyncjob(
    request, headers, user, access_token,
  ):
    data = await request.json()
    
    payload = {}
    
    payload["desc"] = data["desc"] if "desc" in data else None
    payload["body"] = data["body"] if "body" in data else None
    payload["body_json"] = data["body_json"] if "body_json" in data else None
    payload["chat_id"] = data["chat_id"]
    payload["user_id"] = user.id if user != None else None

    item = await ChatMessage.create(**payload)

    return item
  
  return await wrapped_api_task(
    request=request,
    fetch_loggedin_user_info=fetch_loggedin_user_info,
    asyncjob=asyncjob,
    code_success=TAG_C001,
    code_error=TAG_E001,
  )
  
  
  
  
  


@router.delete("/chatmessage")
async def remove(
  request: Request,
  id: str,
  chat_id: str = None,
):
  async def asyncjob(
    request, headers, user, access_token,
  ):
    filters = {}
    filters["chat_id"] = chat_id
    filters["id"] = id

    item = (
      await ChatMessage
        .filter(Q(**filters))
        .first()
    )

    if not item:
      raise HTTPException(status_code=404, detail="ChatMessage not found")


    item.is_deleted = True
    await item.save()

    return item

  return await wrapped_api_task(
    request=request,
    fetch_loggedin_user_info=fetch_loggedin_user_info,
    asyncjob=asyncjob,
    code_success=TAG_C001,
    code_error=TAG_E001,
  )
  
  
  

@router.patch("/chatmessage")
async def update(
  request: Request,
  id: str,
  chat_id: str = None,
):
  async def asyncjob(
    request, headers, user, access_token,
  ):
    filters = {}
    filters["chat_id"] = chat_id
    filters["id"] = id

    item = (
      await ChatMessage
        .filter(Q(**filters))
        .first()
    )

    if not item:
      raise HTTPException(status_code=404, detail="ChatMessage not found")


    data = await request.json()
    
    if "desc" in data:
      item.desc = data["desc"]
    
    if "body" in data:
      item.body = data["body"]
      
    if "body_json" in data:
      item.body_json = data["body_json"]


    await item.save()

    return item

  return await wrapped_api_task(
    request=request,
    fetch_loggedin_user_info=fetch_loggedin_user_info,
    asyncjob=asyncjob,
    code_success=TAG_C001,
    code_error=TAG_E001,
  )
  