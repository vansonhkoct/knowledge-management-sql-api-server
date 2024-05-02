import traceback
from fastapi import APIRouter, File, UploadFile, Form, Request
from fastapi import HTTPException
from typing import Annotated
from tortoise.expressions import Q

import sys
import os

parent_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(parent_dir + "/../../")

router = APIRouter(prefix="/api/v1")


from models.master import Party, User, Role, Permission
from controllers.functions.user.user import create_user


TAG_C001 = "C_PARTY001"
TAG_E001 = "E_PARTY001"




@router.post("/party")
async def party_create(
  request: Request,
):
  try:
    headers = request.headers
    
    payload = {}
    
    party = await Party.create(**payload)
    
    
    
    it_role_superadmin = await Role.create(**{
      "code": "superadmin",
      "party": party,
    })
    
    it_role_admin = await Role.create(**{
      "code": "admin",
      "party": party,
    })

    it_role_staff = await Role.create(**{
      "code": "staff",
      "party": party,
    })
    
    
    
    it_permission_user_manage = await Permission.create(**{
      "code": "user -> manage",
    })
    
    it_permission_category_manage = await Permission.create(**{
      "code": "category -> manage",
    })

    it_permission_file_manage = await Permission.create(**{
      "code": "file -> manage",
    })

    it_permission_role_manage = await Permission.create(**{
      "code": "role -> manage",
    })

    it_permission_permission_manage = await Permission.create(**{
      "code": "permission -> manage",
    })
    
    
    
    it_user_superadmin = await create_user(**{
      "party": party,
      "role": it_role_superadmin,
      "name": "Superadmin",
      "username": "superadmin",
      "password": "123",
    })
    
    it_user_admin = await create_user(**{
      "party": party,
      "role": it_role_admin,
      "name": "Superadmin",
      "username": "admin",
      "password": "123",
    })
    
    it_user_staff = await create_user(**{
      "party": party,
      "role": it_role_staff,
      "name": "Staff 1",
      "username": "s1",
      "password": "123",
    })


    await it_role_superadmin.permissions.add(
      it_permission_user_manage,
      it_permission_category_manage,
      it_permission_file_manage,
      it_permission_role_manage,
      it_permission_permission_manage,
    )
    
    await it_role_admin.permissions.add(
      it_permission_user_manage,
      it_permission_category_manage,
      it_permission_file_manage,
    )


    return {
      "success": True,
      "message": TAG_C001,
      "data": {
        "item": party,
      },
    }

  except Exception as e:
    stacktrace = traceback.format_exc()
    raise HTTPException(
      status_code=500,
      detail={
        "message": TAG_E001,
        "error": str(e),
        "stacktrace": stacktrace,
      }
    )


