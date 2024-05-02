
import sys
import os

parent_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(parent_dir + "/../../../")

from controllers.functions._generic.fileutils import UploadFileRecord, upload_file_write_to_upload_folder
from models.master import File

async def create_entry_file(
  uploadFileRecord: UploadFileRecord = None,
  category_id: str = None,
):
  new_entry = await File.create(
    alias = uploadFileRecord.alias,
    filename = uploadFileRecord.filename,
    mime_type = uploadFileRecord.mimetype,
    size_bytes = uploadFileRecord.filesize,
    category_id = category_id,
  )

  return new_entry



