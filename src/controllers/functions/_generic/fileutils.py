import os
from fastapi import File, UploadFile
from bson import ObjectId
import re
import unicodedata

default_upload_dir = os.getenv("FILE_UPLOAD_ABSOLUTE_PATH") 

class UploadFileRecord:
  def __init__(self, alias: str, filepath: str, filename: str, filesize: int, mimetype: str):
    self.alias = str(alias) if alias != None else None
    self.filepath = str(filepath) if filepath != None else None
    self.filesize = filesize
    self.filename = str(filename) if filename != None else None
    self.mimetype = str(mimetype) if mimetype != None else None


async def upload_file_write_to_upload_folder(
  file: UploadFile,
  upload_dir: str = default_upload_dir,
  alias: str = None,
):
  os.makedirs(upload_dir, exist_ok=True)
  
  filename = makeSafeFilename(file.filename)
  filepath = f"{default_upload_dir}{filename}"

  filebytes = await file.read()

  with open(filepath, "wb") as f:
      f.write(filebytes)

  upload_file_record = UploadFileRecord(
    alias= alias if alias != None else file.filename,
    filepath=filepath,
    filename=filename,
    filesize=file.size,
    mimetype = str(file.content_type) if file.content_type != None else None
  )

  return upload_file_record, filebytes


async def make_file_ref_from_plaintext(
  plaintext: str,
  alias: str = None,
):
  filename = alias if alias is not None else ""
  filepath = ""
  
  filebytes = len(plaintext) if plaintext is not None else 0
  
  upload_file_record = UploadFileRecord(
    alias = alias if alias is not None else "",
    filepath=filepath,
    filename=filename,
    filesize=filebytes,
    mimetype="",
  )
  
  return upload_file_record, filebytes


async def remove_file_from_upload_folder(
  filename: str,
):
  filepath = f"{default_upload_dir}{filename}"

  try:
    # Remove the file from the upload folder
    os.remove(filepath)
  except OSError as e:
    raise e

  return True



def load_uploaded_file(
  filename: str,
):
  filepath = f"{default_upload_dir}{filename}"
  return open(filepath, "rb")



def makeSafeFilename(original_filename):
  object_id = str(ObjectId())
  
  filename = original_filename if original_filename != None else ""
  
    
  def sanitize_filename(filename):
    # Remove special characters
    sanitized_filename = re.sub(r"[^\w\s.-]", "", filename)

    # Normalize filename to ASCII
    normalized_filename = unicodedata.normalize("NFKD", sanitized_filename).encode("ascii", "ignore").decode("ascii")

    # Convert spaces to underscores
    underscored_filename = normalized_filename.replace(" ", "_")

    # Limit filename length
    max_length = 255  # Maximum length allowed by MySQL VARCHAR column
    truncated_filename = underscored_filename[:max_length]

    return truncated_filename
  
  filename = sanitize_filename(filename)
  
  return f"{object_id}_{filename}"



def getStaticFilesBaseUrl():
  return os.getenv("URL_STATIC_BASE_URL")


def getUploadFilesBaseUrl():
  return os.getenv("URL_UPLOAD_BASE_URL")


