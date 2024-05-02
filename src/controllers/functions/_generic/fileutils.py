import os
from fastapi import File, UploadFile

parent_dir = os.path.dirname(os.path.realpath(__file__))
default_upload_dir = parent_dir + "/../../../../upload/"

class UploadFileRecord:
    def __init__(self, file: UploadFile, filepath: str):
        self.file = file
        self.filepath = filepath
        self.filesize = file.size
        self.filename = file.filename,
        self.mimetype = file.content_type,
        print(file.filename, self.filename)

    # def __str__(self):
    #   return self.filename


async def upload_file_write_to_upload_folder(
  file: UploadFile,
  upload_dir: str = default_upload_dir,
):
  os.makedirs(upload_dir, exist_ok=True)
  filepath = f"{default_upload_dir}{file.filename}"

  with open(f"{default_upload_dir}{file.filename}", "wb") as f:
      f.write(await file.read())

  upload_file_record = UploadFileRecord(
    file=file,
    filepath=filepath,
  )

  return upload_file_record
