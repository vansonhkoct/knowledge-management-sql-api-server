
import sys
import os

parent_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(parent_dir + "/../../../")

from controllers.functions._generic.fileutils import UploadFileRecord, upload_file_write_to_upload_folder
from models.master import File

async def create_entry_file(
  uploadFileRecord: UploadFileRecord = None,
):
  new_entry = await File.create(
    filename = uploadFileRecord.file.filename,
    mime_type = uploadFileRecord.file.content_type,
    size_bytes = uploadFileRecord.file.file_size,
  )

  return new_entry



