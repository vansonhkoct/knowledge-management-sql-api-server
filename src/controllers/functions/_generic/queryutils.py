import traceback
from fastapi import APIRouter, File, UploadFile, Form, Request
from fastapi import HTTPException

from tortoise.expressions import Q
from tortoise.models import Model


async def fetch_paginated(
    model: Model,
    filters = {},
    offset = 0,
    limit = 10,
):
    items = (
      await model
        .filter(Q(**filters))
        .offset(offset)
        .limit(limit)
    )
    
    total_count = (
      await model
        .filter(Q(**filters))
        .count()
    )

    tsql = (
      model
        .filter(Q(**filters))
        .sql()
    )

    return items, total_count, tsql




async def fetch_single(
    model: Model,
    filters = {},
):
    item = (
      await model
        .filter(Q(**filters))
        .first()
    )
    
    return item




async def wrapped_api_task(
    request,
    fetch_loggedin_user_info,
    asyncjob,
    code_success,
    code_error,
):
  try:
    headers = request.headers
    user, access_token = await fetch_loggedin_user_info(headers=headers)
    
    data = await asyncjob(
        headers=headers,
        user=user,
        access_token=access_token,
    )
    
    return {
      "success": True,
      "message": code_success,
      "data": data,
    }
  
  except Exception as e:
    stacktrace = traceback.format_exc()
    raise HTTPException(
      status_code=500,
      detail={
        "message": code_error,
        "error": str(e),
        "stacktrace": stacktrace,
      }
    )
    






