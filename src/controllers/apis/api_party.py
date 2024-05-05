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


from models.master import Party, User, Role, Permission, Category
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

    it_role_president = await Role.create(**{
      "code": "president",
      "party": party,
    })

    it_role_executive_officer = await Role.create(**{
      "code": "executive_officer",
      "party": party,
    })

    it_role_school_affairs_officer = await Role.create(**{
      "code": "school_affairs_officer",
      "party": party,
    })

    it_role_teacher = await Role.create(**{
      "code": "teacher",
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

    it_permission_knowledge_search = await Permission.create(**{
      "code": "knowledge -> search",
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
      "name": "Admin",
      "username": "admin",
      "password": "123",
    })
    
    it_user_teacher_1 = await create_user(**{
      "party": party,
      "role": it_role_teacher,
      "name": "Teacher 1",
      "username": "t1",
      "password": "123",
    })
    it_user_teacher_2 = await create_user(**{
      "party": party,
      "role": it_role_teacher,
      "name": "Teacher 2",
      "username": "t2",
      "password": "123",
    })
    it_user_teacher_3 = await create_user(**{
      "party": party,
      "role": it_role_teacher,
      "name": "Teacher 3",
      "username": "t3",
      "password": "123",
    })
    
    it_user_president_1 = await create_user(**{
      "party": party,
      "role": it_role_executive_officer,
      "name": "President 1",
      "username": "p1",
      "password": "123",
    })
    
    it_user_executive_officer_1 = await create_user(**{
      "party": party,
      "role": it_role_executive_officer,
      "name": "Executive Officer 1",
      "username": "eo1",
      "password": "123",
    })
    
    it_user_school_affairs_officer_1 = await create_user(**{
      "party": party,
      "role": it_role_school_affairs_officer,
      "name": "School Affairs Officer 1",
      "username": "sao1",
      "password": "123",
    })
    
    
    
    it_category_EDB = await Category.create(**{
      "alias": "EDB",
      "party": party,
    })
    
    it_category_Diocese = await Category.create(**{
      "alias": "Diocese (教區)",
      "party": party,
    })
    
    it_category_Internal = await Category.create(**{
      "alias": "Internal",
      "party": party,
    })
    
    it_category_Confidential = await Category.create(**{
      "alias": "Confidential",
      "party": party,
      "parent_category": it_category_Internal,
    })
    
    it_category_Financial = await Category.create(**{
      "alias": "Financial",
      "party": party,
      "parent_category": it_category_Internal,
    })
    
    it_category_Internal_Documents = await Category.create(**{
      "alias": "Internal Documents",
      "party": party,
      "parent_category": it_category_Internal,
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

    await it_role_president.permissions.add(
      it_permission_knowledge_search,
    )

    await it_role_executive_officer.permissions.add(
      it_permission_knowledge_search,
    )

    await it_role_school_affairs_officer.permissions.add(
      it_permission_knowledge_search,
    )

    await it_role_teacher.permissions.add(
      it_permission_knowledge_search,
    )
    
    await it_role_president.accessible_categorys.add(
      it_category_EDB,
      it_category_Diocese,
      it_category_Internal_Documents,
      it_category_Confidential,
      it_category_Financial,
    )
    
    await it_role_executive_officer.accessible_categorys.add(
      it_category_EDB,
      it_category_Diocese,
      it_category_Internal_Documents,
      it_category_Confidential,
    )
    
    await it_role_school_affairs_officer.accessible_categorys.add(
      it_category_EDB,
      it_category_Diocese,
      it_category_Internal_Documents,
      it_category_Financial,
    )
    
    await it_role_teacher.accessible_categorys.add(
      it_category_EDB,
      it_category_Diocese,
      it_category_Internal_Documents,
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


