import traceback
from fastapi import APIRouter, File, UploadFile, Form, Request
from fastapi import HTTPException
from typing import Annotated
from tortoise.expressions import Q

import sys
import os

parent_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(parent_dir + "/../../")

from controllers.functions.user.userauth_email import obtain_user_by_user_credential

from controllers.functions.user.userauth_session import obtain_user_by_user_access_token
from controllers.functions.user.userauth_session import create_new_access_token_by_user_refresh_token
from controllers.functions.user.userauth_session import create_new_access_token_and_refresh_token_by_user
from controllers.functions.user.userauth_session import delete_access_token

router = APIRouter(prefix="/api/v1")



TAG_C001 = "C_AUTH001"
TAG_E001 = "E_AUTH001"




@router.post("/auth/login")
async def auth_login(
  request: Request,
):
  try:
    headers = request.headers
    
    data = await request.json()
    
    user = await obtain_user_by_user_credential(
      username=data["username"],
      password=data["password"],
    )
    
    userSession = await create_new_access_token_and_refresh_token_by_user(
      user=user,
    )
  
    return {
      "success": True,
      "message": TAG_C001,
      "data": {
        "item": {
          "user": user,
          "userSession": userSession,
        },
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



@router.post("/auth/logout")
async def auth_logout(
  request: Request,
):
  try:
    headers = request.headers
    
    
  
    return {
      "success": True,
      "message": TAG_C001,
      "data": {

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


