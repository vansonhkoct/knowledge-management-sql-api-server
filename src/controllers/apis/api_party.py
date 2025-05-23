import traceback
from fastapi import APIRouter, File, UploadFile, Form, Request
from fastapi import HTTPException
from typing import Annotated
from tortoise.expressions import Q

from src.controllers.functions.user.user import create_user
from src.controllers.functions.user.userauth_session import fetch_loggedin_user_info
from src.controllers.functions._generic.queryutils import fetch_paginated, fetch_single, wrapped_api_task

from src.models.master import Party, User, Role, Permission, Category


router = APIRouter(prefix="/api/v1")


TAG_C001 = "C_PARTY001"
TAG_E001 = "E_PARTY001"




@router.get("/party")
async def fetch(
  request: Request,
  page: int = 0,
  limit: int = 10,
):
  async def asyncjob(
    headers, user, access_token,
  ):
    # Calculate the offset based on the page and limit
    offset = (page) * limit
    
    # Fetch the category items from the database using Tortoise ORM
    filters = {}
    
    filters["is_disabled"] = False
    filters["is_deleted"] = False

    items, total_count, tsql = await fetch_paginated(
      model=Party,
      filters=filters,
      offset=offset,
      limit=limit,
    )
    
    return {
      "filters": filters,
      "sql": tsql,
      "pagination": {
        "page": page,
        "limit": limit,
        "total_count": total_count,
      },
      "items": items,
    }
  
  return await wrapped_api_task(
    request=request,
    fetch_loggedin_user_info=fetch_loggedin_user_info,
    asyncjob=asyncjob,
    code_success=TAG_C001,
    code_error=TAG_E001,
  )
  


@router.get("/party/single")
async def fetchSingle(
  request: Request,
  id: str,
):
  async def asyncjob(
    headers, user, access_token,
  ):
    filters = {}
    filters["id"] = id
    filters["is_disabled"] = False
    filters["is_deleted"] = False

    item = await fetch_single(
      model=Party,
      filters=filters,
    )

    return item
  
  return await wrapped_api_task(
    request=request,
    fetch_loggedin_user_info=fetch_loggedin_user_info,
    asyncjob=asyncjob,
    code_success=TAG_C001,
    code_error=TAG_E001,
  )
  
  
  


@router.post("/party/create_default")
async def party_create(
  request: Request,
):
  try:
    headers = request.headers
    
    data = await request.json()

    name = data["name"] if "name" in data else ""
    prefix = data["prefix"] if "prefix" in data else ""
    password = data["password"] if "password" in data else "123"
    
    
    
    payload = {
      "name": name,
    }
    
    party = await Party.create(**payload)
    
    
    
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
    
    
    
    it_permission_user_manage = await Permission.filter(**{
      "code": "user -> manage",
    }).first()
    
    it_permission_category_manage = await Permission.filter(**{
      "code": "category -> manage",
    }).first()

    it_permission_file_manage = await Permission.filter(**{
      "code": "file -> manage",
    }).first()

    it_permission_role_manage = await Permission.filter(**{
      "code": "role -> manage",
    }).first()

    it_permission_role_accessible_category_manage = await Permission.filter(**{
      "code": "role -> accessible_category -> manage",
    }).first()

    it_permission_permission_manage = await Permission.filter(**{
      "code": "permission -> manage",
    }).first()

    it_permission_knowledge_search = await Permission.filter(**{
      "code": "knowledge -> search",
    }).first()
    
    
    
    it_user_admin = await create_user(**{
      "party_id": party.id,
      "role_id": it_role_admin.id,
      "name": "Admin",
      "username": f"{prefix}admin",
      "password": password,
    })
    
    it_user_teacher_1 = await create_user(**{
      "party_id": party.id,
      "role_id": it_role_teacher.id,
      "name": "Teacher 1",
      "username": f"{prefix}t1",
      "password": password,
    })
    it_user_teacher_2 = await create_user(**{
      "party_id": party.id,
      "role_id": it_role_teacher.id,
      "name": "Teacher 2",
      "username": f"{prefix}t2",
      "password": password,
    })
    it_user_teacher_3 = await create_user(**{
      "party_id": party.id,
      "role_id": it_role_teacher.id,
      "name": "Teacher 3",
      "username": f"{prefix}t3",
      "password": password,
    })
    
    it_user_president_1 = await create_user(**{
      "party_id": party.id,
      "role_id": it_role_president.id,
      "name": "President 1",
      "username": f"{prefix}p1",
      "password": password,
    })
    
    it_user_executive_officer_1 = await create_user(**{
      "party_id": party.id,
      "role_id": it_role_executive_officer.id,
      "name": "Executive Officer 1",
      "username": f"{prefix}eo1",
      "password": password,
    })
    
    it_user_school_affairs_officer_1 = await create_user(**{
      "party_id": party.id,
      "role_id": it_role_school_affairs_officer.id,
      "name": "School Affairs Officer 1",
      "username": f"{prefix}sao1",
      "password": password,
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

    
    
    

    
    await it_role_admin.permissions.add(
      it_permission_user_manage,
      it_permission_file_manage,
      it_permission_role_manage,
      it_permission_role_accessible_category_manage,
      it_permission_knowledge_search,
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



@router.post("/party/create_superadmin_party")
async def party_create_superadmin_party(
  request: Request,
):
  try:
    headers = request.headers
    
    data = await request.json()

    name = data["name"] if "name" in data else ""
    prefix = data["prefix"] if "prefix" in data else ""
    password = data["password"] if "password" in data else "123"
    

    payload = {
      "name": name,
    }

    party = await Party.create(**payload)
    
    it_role_superadmin = await Role.create(**{
      "code": "superadmin",
      "party": party,
    })
    
    it_permission_superadmin_manage_partys = await Permission.create(**{
      "code": "superadmin -> manage_partys",
    })
    
    it_permission_superadmin_manage_shared_categorys = await Permission.create(**{
      "code": "superadmin -> manage_shared_categorys",
    })
    
    
    it_user_superadmin = await create_user(**{
      "party_id": party.id,
      "role_id": it_role_superadmin.id,
      "name": "Superadmin",
      "username": f"{prefix}superadmin",
      "password": password,
    })
    
    
    await it_role_superadmin.permissions.add(
      it_permission_superadmin_manage_partys,
      it_permission_superadmin_manage_shared_categorys,
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
    
    
    
    