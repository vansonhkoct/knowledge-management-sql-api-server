from fastapi import APIRouter, File, UploadFile, Form, Request
from typing import Annotated

import sys
import os

parent_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(parent_dir + "/../../")

from controllers.functions._generic.fileutils import UploadFileRecord, upload_file_write_to_upload_folder
from controllers.functions.file.file import create_entry_file

router = APIRouter(prefix="/api/v1")


@router.post("/files/upload")
async def upload_and_create(
  request: Request,
  category_id: Annotated[str, Form()] = None,
  # file: UploadFile = File(...),
  file: UploadFile = File(),
):
    headers = request.headers
  
    # Save the uploaded file to the local "./upload" folder
    file_ref = await upload_file_write_to_upload_folder(
      file=file,
    )
    
    file_entry = await create_entry_file(
      uploadFileRecord = file_ref,
    )
    
    return {
      "success": True,
      "message": "C_F001",
      "data": {
        "item": file_entry,
        "c": category_id,
      },
    }

