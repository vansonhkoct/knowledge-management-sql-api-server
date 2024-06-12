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



from models.master import ChatMessageFeedback
from controllers.functions.user.userauth_session import fetch_loggedin_user_info
from controllers.functions._generic.queryutils import fetch_paginated, wrapped_api_task



TAG_C001 = "C_CHATMESSAGEFEEDBACK001"
TAG_E001 = "E_CHATMESSAGEFEEDBACK001"



@router.get("/chatmessagefeedback/single")
async def fetchSingle(
  request: Request,
  chatmessage_id: str = None,
):
  async def asyncjob(
    request, headers, user, access_token,
  ):
    # Fetch the permission items from the database using Tortoise ORM
    filters = {}
    filters["chatmessage_id"] = chatmessage_id
    filters["user_id"] = user.id
    filters["is_disabled"] = False
    filters["is_deleted"] = False

    item = (
      await ChatMessageFeedback
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
  




@router.patch("/chatmessagefeedback")
async def upsert(
  request: Request,
  chatmessage_id: str = None,
):
  async def asyncjob(
    request, headers, user, access_token,
  ):
    data = await request.json()

    filters = {}
    filters["chatmessage_id"] = chatmessage_id
    filters["user_id"] = user.id
    filters["is_disabled"] = False
    filters["is_deleted"] = False

    item = (
      await ChatMessageFeedback
        .filter(Q(**filters))
        .first()
    )

    if not item:
      
      payload = {}

      if "desc" in data:
        payload["desc"] = data["desc"]

      if "body" in data:
        payload["body"] = data["body"]

      if "body_json" in data:
        payload["body_json"] = data["body_json"]

      if "score" in data:
        payload["score"] = data["score"]

      if "is_like" in data:
        payload["is_like"] = data["is_like"]

      if "is_dislike" in data:
        payload["is_dislike"] = data["is_dislike"]

      item = await ChatMessageFeedback.create(**payload)

      
    else:

      if "desc" in data:
        item.desc = data["desc"]

      if "body" in data:
        item.body = data["body"]

      if "body_json" in data:
        item.body_json = data["body_json"]

      if "score" in data:
        item.score = data["score"]

      if "is_like" in data:
        item.is_like = data["is_like"]

      if "is_dislike" in data:
        item.is_dislike = data["is_dislike"]

      await item.save()

    return item

  return await wrapped_api_task(
    request=request,
    fetch_loggedin_user_info=fetch_loggedin_user_info,
    asyncjob=asyncjob,
    code_success=TAG_C001,
    code_error=TAG_E001,
  )
  


@router.delete("/chatmessagefeedback")
async def remove(
  request: Request,
  chatmessage_id: str = None,
):
  async def asyncjob(
    request, headers, user, access_token,
  ):
    filters = {}
    filters["chatmessage_id"] = chatmessage_id
    filters["user_id"] = user.id
    filters["is_disabled"] = False
    filters["is_deleted"] = False

    item = (
      await ChatMessageFeedback
        .filter(Q(**filters))
        .first()
    )

    if not item:
      raise HTTPException(status_code=404, detail="ChatMessageFeedback not found")


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
  
  
  
