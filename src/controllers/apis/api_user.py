import traceback
from fastapi import APIRouter, File, UploadFile, Form, Request
from fastapi import HTTPException
from typing import Annotated
from tortoise.expressions import Q

import sys
import os

parent_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(parent_dir + "/../../")

from controllers.functions.user.user import create_user
from controllers.functions.user.userauth_session import fetch_loggedin_user_info, delete_access_token

router = APIRouter(prefix="/api/v1")

from models.master import User, Role, Permission, UserCredential, UserCredentialType


TAG_C001 = "C_USER001"
TAG_E001 = "E_USER001"




@router.get("/user/me")
async def user_me(
  request: Request,
):
  headers = request.headers
  user = await fetch_loggedin_user_info(headers=headers)

  try:
    return {
      "success": True,
      "message": TAG_C001,
      "data": {
        "item": user,
      }
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



@router.post("/user/logout")
async def user_logout(
  request: Request,
):
  headers = request.headers
  user, access_token = await fetch_loggedin_user_info(headers=headers)

  try:
    await delete_access_token(access_token=access_token)
    
    return {
      "success": True,
      "message": TAG_C001,
      "data": {
        "item": user,
      }
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










@router.post("/user")
async def user_create(
  request: Request,
):
  try:
    headers = request.headers

    data = await request.json()

    role_id = data["role_id"] if "role_id" in data else None
    role = await Role.filter(id=role_id).first()

    username = data["username"] if "username" in data else ""
    password = data["password"] if "password" in data else ""
    
    item = await create_user(
      role=role,
      username=username,
      password=password,
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



