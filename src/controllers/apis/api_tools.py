import traceback
from fastapi import APIRouter, File, UploadFile, Form, Request
from fastapi import HTTPException
from typing import Annotated
from tortoise.expressions import Q

import sys
import os

import uuid

parent_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(parent_dir + "/../../")

router = APIRouter(prefix="/api/v1")


TAG_C001 = "C_TOOL001"
TAG_E001 = "E_TOOL001"




@router.get("/tool/gen_uuid")
async def tool_gen_uuid(
  request: Request,
):
  try:
    headers = request.headers
    


    return {
      "success": True,
      "message": TAG_C001,
      "data": {
        "uuid": str(uuid.uuid4()),
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





