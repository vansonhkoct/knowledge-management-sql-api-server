import traceback

import sys
import os

parent_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(parent_dir + "/../../../")

from controllers.functions._generic.fileutils import UploadFileRecord, upload_file_write_to_upload_folder
from controllers.functions._generic.modelutils import hashPassword, checkPassword
from controllers.functions.file.file import create_entry_file

from models.master import User, UserCredential, UserCredentialType



def make_user_credential(
  username: str,
  password: str,
):
  try:
    item = UserCredential(**{
      "credential_type": UserCredentialType.EMAIL,
      "status": "ACTIVATED",
      "username": username,
      "password_hash": hashPassword(password=password)
    })

    return item

  except Exception as e:
    raise e



async def obtain_user_by_user_credential(
  username: str,
  password: str,
):
  try:
    item = await UserCredential.filter(**{
      "credential_type": UserCredentialType.EMAIL,
      "status": "ACTIVATED",
      "username": username,
    }).first()
    
    if (checkPassword(
      hashed_password=item.password_hash,
      password=password,
    )):
      await item.fetch_related("user")
      return item.user
  
    return None
  
  except Exception as e:
    raise e



