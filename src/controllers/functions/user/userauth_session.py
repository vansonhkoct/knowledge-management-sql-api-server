import traceback
from fastapi import HTTPException

import sys
import os

parent_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(parent_dir + "/../../../")

from controllers.functions._generic.fileutils import UploadFileRecord, upload_file_write_to_upload_folder
from controllers.functions._generic.modelutils import makeUuid
from controllers.functions.file.file import create_entry_file

from models.master import User, UserSession



async def obtain_user_by_user_access_token(
  access_token: str,
):
  try:
    item = await UserSession.filter(**{
      "access_token": access_token,
    }).prefetch_related("user").first()
    
    if item == None:
      raise HTTPException(
        status_code=403,
      )

    await item.user.fetch_related("role__permissions")
    return item.user if item != None else None

  except Exception as e:
    raise e




async def create_new_access_token_by_user_refresh_token(
  refresh_token: str,
):
  try:
    new_access_token = None
    new_refresh_token = None

    item = await UserSession.filter(**{
      "refresh_token": refresh_token,
    }).prefetch_related("user").first()

    new_item = None

    if (item != None and item.user != None):
      new_access_token = makeUuid()
      new_refresh_token = refresh_token

      new_item = await UserSession.create(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
      )

    return new_item

  except Exception as e:
    raise e





async def create_new_access_token_and_refresh_token_by_user(
  user: User,
):
  try:
    new_item = await UserSession.create(
      user=user,
      access_token=makeUuid(),
      refresh_token=makeUuid(),
    )
    return new_item

  except Exception as e:
    raise e



async def fetch_loggedin_user_info(headers):
  user = None
  access_token = None
  
  try:
    authorization_header = headers["authorization"]
    if authorization_header.startswith("Bearer "):
        access_token = authorization_header.split(" ")[1]
        user = await obtain_user_by_user_access_token(access_token=access_token)
        
  except Exception as e:
    raise e
  
  if user == None:
    raise HTTPException(
      status_code=403,
    )

  return user, access_token

async def delete_access_token(
  access_token: str,
):
  try:
    await UserSession.filter(
      access_token=access_token,
    ).delete()

  except Exception as e:
    raise e








