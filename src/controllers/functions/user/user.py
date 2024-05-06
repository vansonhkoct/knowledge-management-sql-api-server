import traceback

import sys
import os

parent_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(parent_dir + "/../../../")

from controllers.functions.user.userauth_email import make_user_credential
from models.master import User, Role, Party


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
  })

  item_userCredential = make_user_credential(username=username, password=password)
  item_userCredential.user_id = item.id
  await item_userCredential.save()

  return item
