import traceback
from fastapi import APIRouter, File, UploadFile, Form, Request
from fastapi import HTTPException
from typing import Annotated
from tortoise.expressions import Q

import sys
import os

parent_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(parent_dir + "/../../")

from controllers.functions._generic.fileutils import UploadFileRecord, upload_file_write_to_upload_folder
from controllers.functions.file.file import create_entry_file

router = APIRouter(prefix="/api/v1")

from models.master import User, Role, Permission


TAG_C001 = "C_USER001"
TAG_E001 = "E_USER001"



@router.post("/permission")
async def permission_create(
  request: Request,
):
  try:
    headers = request.headers
    
    payload = {}
    
    item = await Permission.create(**payload)

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


