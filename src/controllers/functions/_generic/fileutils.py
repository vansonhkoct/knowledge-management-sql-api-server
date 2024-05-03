import os
from fastapi import File, UploadFile
from bson import ObjectId
import re
import unicodedata

parent_dir = os.path.dirname(os.path.realpath(__file__))
default_upload_dir = parent_dir + "/../../../../upload/"

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

  with open(filepath, "wb") as f:
      f.write(await file.read())

  upload_file_record = UploadFileRecord(
    alias= alias if alias != None else file.filename,
    filepath=filepath,
    filename=filename,
    filesize=file.size,
    mimetype = str(file.content_type) if file.content_type != None else None
  )

  return upload_file_record



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
  return "http://localhost:17891/static/"


def getUploadFilesBaseUrl():
  return "http://localhost:17891/upload/"


