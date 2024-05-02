from fastapi import APIRouter, File, UploadFile

import sys
import os

parent_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(parent_dir + "/../../")

from controllers.functions._generic.fileutils import UploadFileRecord, upload_file_write_to_upload_folder
from controllers.functions.file.file import create_entry_file

router = APIRouter(prefix="/api/v1")


@router.post("/files/")
async def upload_and_create_file(file: UploadFile = File(...)):
    # Save the uploaded file to the local "./upload" folder
    file_ref = upload_file_write_to_upload_folder(
      file=file,
    )
    
    file_entry = create_entry_file(
      uploadFileRecord = file_ref,
    )
    
    return {
      "success": True,
      "message": "C_F001",
      "data": file_entry,
    }

