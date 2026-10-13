import os
from fastapi import File, UploadFile
import re
import unicodedata
import uuid

default_upload_dir = os.getenv("FILE_UPLOAD_ABSOLUTE_PATH") 


def _get_upload_dir(upload_dir: str | None = None):
  return upload_dir or default_upload_dir or "./upload"


def _build_upload_filepath(filename: str, upload_dir: str | None = None):
  return os.path.join(_get_upload_dir(upload_dir), filename)


def _build_legacy_upload_filepath(filename: str, upload_dir: str | None = None):
  return f"{_get_upload_dir(upload_dir)}{filename}"


def _resolve_existing_upload_filepath(filename: str, upload_dir: str | None = None):
  filepath = _build_upload_filepath(filename, upload_dir)
  if os.path.exists(filepath):
    return filepath

  legacy_filepath = _build_legacy_upload_filepath(filename, upload_dir)
  if os.path.exists(legacy_filepath):
    os.makedirs(_get_upload_dir(upload_dir), exist_ok=True)
    os.replace(legacy_filepath, filepath)
    return filepath

  return filepath

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
  upload_dir = _get_upload_dir(upload_dir)
  os.makedirs(upload_dir, exist_ok=True)
  
  filename = makeSafeFilename(file.filename)
  filepath = _build_upload_filepath(filename, upload_dir)

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
  upload_dir = _get_upload_dir(default_upload_dir)
  os.makedirs(upload_dir, exist_ok=True)

  display_name = alias if alias not in [None, ""] else "plaintext.txt"
  if "." not in display_name:
    display_name = f"{display_name}.txt"

  filename = makeSafeFilename(display_name)
  filepath = _build_upload_filepath(filename, upload_dir)
  filebytes = (plaintext or "").encode("utf-8")

  with open(filepath, "wb") as f:
    f.write(filebytes)
  
  upload_file_record = UploadFileRecord(
    alias = alias if alias is not None else display_name,
    filepath=filepath,
    filename=filename,
    filesize=len(filebytes),
    mimetype="text/plain",
  )
  
  return upload_file_record, filebytes


async def remove_file_from_upload_folder(
  filename: str,
):
  filepath = _resolve_existing_upload_filepath(filename, default_upload_dir)

  try:
    # Remove the file from the upload folder
    os.remove(filepath)
  except OSError as e:
    raise e

  return True



def load_uploaded_file(
  filename: str,
):
  filepath = _resolve_existing_upload_filepath(filename, default_upload_dir)
  return open(filepath, "rb")


def resolve_uploaded_file_path(filename: str):
  if not filename or os.path.basename(filename) != filename:
    raise ValueError("Invalid stored filename")
  return _resolve_existing_upload_filepath(filename, default_upload_dir)



def makeSafeFilename(original_filename):
  object_id = uuid.uuid4().hex[:24]
  
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
