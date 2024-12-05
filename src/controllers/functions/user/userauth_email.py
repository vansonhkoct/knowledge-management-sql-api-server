import traceback

from tortoise.expressions import Q

from src.controllers.functions._generic.fileutils import UploadFileRecord, upload_file_write_to_upload_folder
from src.controllers.functions._generic.modelutils import hashPassword, checkPassword
from ..file.file import create_entry_file

from src.models.master import User, UserCredential, UserCredentialType



def make_password_hash(
  password: str,
):
  try:
    return hashPassword(password=password)
  except Exception as e:
    raise e


def check_password_hash(
  password_hash: str,
  password: str,
):
  try:
    return (checkPassword(
      hashed_password=password_hash,
      password=password,
    ))
  except Exception as e:
    raise e



def make_user_credential(
  user_id: str,
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
    
    item.user_id = user_id

    return item

  except Exception as e:
    raise e


async def remake_user_credential(
  user_id: str,
  password: str,
):
  try:
    filters = {}
    filters["user_id"] = user_id
    filters["credential_type"] = UserCredentialType.EMAIL

    item = (
      await UserCredential
        .filter(Q(**filters))
        .first()
    )
    
    if item:
      item.password_hash = hashPassword(password=password)
      
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
    
    if not item:
      return None
    
    if (checkPassword(
      hashed_password=item.password_hash,
      password=password,
    )):
      await item.fetch_related("user")
      return item.user
  
    return None
  
  except Exception as e:
    raise e



async def obtain_user_by_user_credential_and_party_id(
  username: str,
  password: str,
  party_id: str,
):
  try:
    item = await UserCredential.filter(**{
      "user__party_id": party_id,
      "credential_type": UserCredentialType.EMAIL,
      "status": "ACTIVATED",
      "username": username,
    }).first()
        
    if not item:
      return None

    if (checkPassword(
      hashed_password=item.password_hash,
      password=password,
    )):
      await item.fetch_related("user")
      return item.user
  
    return None
  
  except Exception as e:
    raise e

