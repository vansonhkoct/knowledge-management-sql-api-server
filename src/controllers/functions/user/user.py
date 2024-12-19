import traceback

from .userauth_email import make_user_credential, remake_user_credential
from src.models.master import User, Role, Party


async def create_user(
  party_id: str = None,
  role_id: str = None,
  name: str = None,
  username: str = None,
  password: str = None,
):
  item = await User.create(**{
    "party_id": party_id,
    "role_id": role_id,
    "name": name,
    "username": username,
  })

  item_userCredential = make_user_credential(user_id=item.id, password=password)
  await item_userCredential.save()

  return item



async def update_user_password(
  user_id: str,
  password: str,
):
  item_userCredential = await remake_user_credential(user_id=user_id, password=password)
  await item_userCredential.save()
