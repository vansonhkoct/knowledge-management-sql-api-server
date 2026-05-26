import traceback
from fastapi import APIRouter, File, UploadFile, Form, Request
from fastapi import HTTPException
from typing import Annotated
from tortoise.expressions import Q
from tortoise.transactions import atomic

from src.controllers.functions.user.user import create_user
from src.controllers.functions.user.userauth_session import fetch_loggedin_user_info
from src.controllers.functions.user.userscope import can_manage_other_parties, ensure_can_manage_other_parties
from src.controllers.functions._generic.queryutils import fetch_paginated, fetch_single, wrapped_api_task

from src.models.master import Party, User, Role, Permission, Category, AIModelEndpoint


router = APIRouter(prefix="/api/v1")


TAG_C001 = "C_PARTY001"
TAG_E001 = "E_PARTY001"

MODEL_TYPE_LLM = "LLM"
MODEL_TYPE_EMBEDDING = "EMBEDDING"


def _normalize_model_type(value: str | None):
  if value in [None, ""]:
    return None

  normalized = str(value).strip().upper()
  if normalized not in [MODEL_TYPE_LLM, MODEL_TYPE_EMBEDDING]:
    raise HTTPException(status_code=400, detail=f"Unsupported model_type: {value}")
  return normalized


async def _fetch_ai_model_endpoint(endpoint_id: str | None, model_type: str | None = None):
  if endpoint_id in [None, ""]:
    return None

  filters = {
    "id": endpoint_id,
    "is_disabled": False,
    "is_deleted": False,
  }
  if model_type is not None:
    filters["model_type"] = _normalize_model_type(model_type)

  item = await AIModelEndpoint.filter(**filters).first()
  if item is None:
    raise HTTPException(status_code=400, detail=f"Model endpoint not found: {endpoint_id}")

  return item


async def _serialize_ai_model_endpoint(item: AIModelEndpoint | None):
  if item is None:
    return None

  return {
    "id": str(item.id),
    "name": item.name,
    "desc": item.desc,
    "model_type": item.model_type,
    "provider": item.provider,
    "base_url": item.base_url,
    "api_path": item.api_path,
    "api_key": item.api_key,
    "model_name": item.model_name,
    "headers_json": item.headers_json,
    "options_json": item.options_json,
    "is_disabled": item.is_disabled,
    "is_deleted": item.is_deleted,
    "created_at": item.created_at,
    "modified_at": item.modified_at,
  }


async def _serialize_party(item: Party | None):
  if item is None:
    return None

  await item.fetch_related("default_llm_model", "default_embedding_model")

  return {
    "id": str(item.id),
    "name": item.name,
    "desc": item.desc,
    "is_disabled": item.is_disabled,
    "is_deleted": item.is_deleted,
    "created_at": item.created_at,
    "modified_at": item.modified_at,
    "default_llm_model_id": str(item.default_llm_model_id) if item.default_llm_model_id else None,
    "default_embedding_model_id": str(item.default_embedding_model_id) if item.default_embedding_model_id else None,
    "default_llm_model": await _serialize_ai_model_endpoint(item.default_llm_model),
    "default_embedding_model": await _serialize_ai_model_endpoint(item.default_embedding_model),
  }


async def _fetch_existing_party_by_username(username: str | None):
  if username in [None, ""]:
    return None

  existing_user = await User.filter(
    username=username,
    is_deleted=False,
  ).first()

  if existing_user is None or existing_user.party_id is None:
    return None

  return await Party.filter(
    id=existing_user.party_id,
    is_disabled=False,
    is_deleted=False,
  ).first()


async def _get_or_create_global_permission(code: str):
  permission = await Permission.filter(
    code=code,
    is_deleted=False,
  ).order_by("created_at").first()

  if permission is None:
    permission = await Permission.create(**{
      "code": code,
    })

  return permission




@router.get("/party")
async def fetch(
  request: Request,
  page: int = 0,
  limit: int = 10,
  party_id: str = None,
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

    if can_manage_other_parties(user):
      if party_id not in [None, ""]:
        filters["id"] = party_id
    else:
      filters["id"] = user.party_id

    items, total_count, tsql = await fetch_paginated(
      model=Party,
      filters=filters,
      offset=offset,
      limit=limit,
    )

    serialized_items = [await _serialize_party(item) for item in items]
    
    return {
      "filters": filters,
      "sql": tsql,
      "pagination": {
        "page": page,
        "limit": limit,
        "total_count": total_count,
      },
      "items": serialized_items,
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

    if not can_manage_other_parties(user):
      filters["id"] = user.party_id

    item = await fetch_single(
      model=Party,
      filters=filters,
    )

    return await _serialize_party(item)
  
  return await wrapped_api_task(
    request=request,
    fetch_loggedin_user_info=fetch_loggedin_user_info,
    asyncjob=asyncjob,
    code_success=TAG_C001,
    code_error=TAG_E001,
  )
  
  
  


@router.post("/party/create_default")
@atomic()
async def party_create_default(
  request: Request,
):
  try:
    headers = request.headers
    
    data = await request.json()

    name = data["name"] if "name" in data else ""
    prefix = data["prefix"] if "prefix" in data else ""
    password = data["password"] if "password" in data else "123"

    existing_party = await _fetch_existing_party_by_username(f"{prefix}admin")
    if existing_party is not None:
      return {
        "success": True,
        "message": TAG_C001,
        "data": {
          "item": await _serialize_party(existing_party),
          "already_exists": True,
        },
      }
    
    
    
    payload = {
      "name": name,
    }

    default_llm_model = await _fetch_ai_model_endpoint(
      data["default_llm_model_id"] if "default_llm_model_id" in data else None,
      model_type=MODEL_TYPE_LLM,
    )
    default_embedding_model = await _fetch_ai_model_endpoint(
      data["default_embedding_model_id"] if "default_embedding_model_id" in data else None,
      model_type=MODEL_TYPE_EMBEDDING,
    )

    if default_llm_model is not None:
      payload["default_llm_model_id"] = default_llm_model.id

    if default_embedding_model is not None:
      payload["default_embedding_model_id"] = default_embedding_model.id
    
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
        "item": await _serialize_party(party),
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


@router.post("/party")
async def party_create(
  request: Request,
):
  try:
    headers = request.headers
    user, access_token = await fetch_loggedin_user_info(headers=headers)

    ensure_can_manage_other_parties(user)

    data = await request.json()

    payload = {
      "name": data["name"] if "name" in data else "",
      "desc": data["desc"] if "desc" in data else None,
    }

    default_llm_model = await _fetch_ai_model_endpoint(
      data["default_llm_model_id"] if "default_llm_model_id" in data else None,
      model_type=MODEL_TYPE_LLM,
    )
    default_embedding_model = await _fetch_ai_model_endpoint(
      data["default_embedding_model_id"] if "default_embedding_model_id" in data else None,
      model_type=MODEL_TYPE_EMBEDDING,
    )

    payload["default_llm_model_id"] = default_llm_model.id if default_llm_model is not None else None
    payload["default_embedding_model_id"] = default_embedding_model.id if default_embedding_model is not None else None

    item = await Party.create(**payload)

    return {
      "success": True,
      "message": TAG_C001,
      "data": {
        "item": await _serialize_party(item),
      },
    }

  except HTTPException as e:
    raise e

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


@router.patch("/party")
async def party_update(
  request: Request,
  id: str,
):
  try:
    headers = request.headers
    user, access_token = await fetch_loggedin_user_info(headers=headers)

    ensure_can_manage_other_parties(user)

    item = await Party.filter(
      id=id,
      is_disabled=False,
      is_deleted=False,
    ).first()

    if not item:
      raise HTTPException(status_code=404, detail="Party not found")

    data = await request.json()

    if "name" in data:
      item.name = data["name"]

    if "desc" in data:
      item.desc = data["desc"]

    if "default_llm_model_id" in data:
      default_llm_model = await _fetch_ai_model_endpoint(
        data["default_llm_model_id"],
        model_type=MODEL_TYPE_LLM,
      )
      item.default_llm_model_id = default_llm_model.id if default_llm_model is not None else None

    if "default_embedding_model_id" in data:
      default_embedding_model = await _fetch_ai_model_endpoint(
        data["default_embedding_model_id"],
        model_type=MODEL_TYPE_EMBEDDING,
      )
      item.default_embedding_model_id = default_embedding_model.id if default_embedding_model is not None else None

    await item.save()

    return {
      "success": True,
      "message": TAG_C001,
      "data": {
        "item": await _serialize_party(item),
      },
    }

  except HTTPException as e:
    raise e

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
@atomic()
async def party_create_superadmin_party(
  request: Request,
):
  try:
    headers = request.headers
    
    data = await request.json()

    name = data["name"] if "name" in data else ""
    prefix = data["prefix"] if "prefix" in data else ""
    password = data["password"] if "password" in data else "123"

    existing_party = await _fetch_existing_party_by_username(f"{prefix}superadmin")
    if existing_party is not None:
      return {
        "success": True,
        "message": TAG_C001,
        "data": {
          "item": await _serialize_party(existing_party),
          "already_exists": True,
        },
      }
    

    payload = {
      "name": name,
    }

    default_llm_model = await _fetch_ai_model_endpoint(
      data["default_llm_model_id"] if "default_llm_model_id" in data else None,
      model_type=MODEL_TYPE_LLM,
    )
    default_embedding_model = await _fetch_ai_model_endpoint(
      data["default_embedding_model_id"] if "default_embedding_model_id" in data else None,
      model_type=MODEL_TYPE_EMBEDDING,
    )

    if default_llm_model is not None:
      payload["default_llm_model_id"] = default_llm_model.id

    if default_embedding_model is not None:
      payload["default_embedding_model_id"] = default_embedding_model.id

    party = await Party.create(**payload)
    
    it_role_superadmin = await Role.create(**{
      "code": "superadmin",
      "party": party,
    })
    
    it_permission_superadmin_manage_partys = await _get_or_create_global_permission(
      "superadmin -> manage_partys",
    )
    
    it_permission_superadmin_manage_shared_categorys = await _get_or_create_global_permission(
      "superadmin -> manage_shared_categorys",
    )
    
    
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
        "item": await _serialize_party(party),
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


@router.get("/ai_model_endpoint")
async def fetch_ai_model_endpoint_list(
  request: Request,
  page: int = 0,
  limit: int = 100,
  model_type: str = None,
):
  async def asyncjob(headers, user, access_token):
    ensure_can_manage_other_parties(user)

    filters = {
      "is_disabled": False,
      "is_deleted": False,
    }

    normalized_model_type = _normalize_model_type(model_type)
    if normalized_model_type is not None:
      filters["model_type"] = normalized_model_type

    offset = page * limit
    items, total_count, tsql = await fetch_paginated(
      model=AIModelEndpoint,
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
      "items": [await _serialize_ai_model_endpoint(item) for item in items],
    }

  return await wrapped_api_task(
    request=request,
    fetch_loggedin_user_info=fetch_loggedin_user_info,
    asyncjob=asyncjob,
    code_success=TAG_C001,
    code_error=TAG_E001,
  )


@router.get("/ai_model_endpoint/single")
async def fetch_ai_model_endpoint_single(
  request: Request,
  id: str,
):
  async def asyncjob(headers, user, access_token):
    ensure_can_manage_other_parties(user)
    item = await AIModelEndpoint.filter(
      id=id,
      is_disabled=False,
      is_deleted=False,
    ).first()
    return await _serialize_ai_model_endpoint(item)

  return await wrapped_api_task(
    request=request,
    fetch_loggedin_user_info=fetch_loggedin_user_info,
    asyncjob=asyncjob,
    code_success=TAG_C001,
    code_error=TAG_E001,
  )


@router.post("/ai_model_endpoint")
async def ai_model_endpoint_create(
  request: Request,
):
  try:
    headers = request.headers
    user, access_token = await fetch_loggedin_user_info(headers=headers)

    ensure_can_manage_other_parties(user)

    data = await request.json()
    item = await AIModelEndpoint.create(**{
      "name": data["name"] if "name" in data else "",
      "desc": data["desc"] if "desc" in data else None,
      "model_type": _normalize_model_type(data["model_type"] if "model_type" in data else None),
      "provider": data["provider"] if "provider" in data else "openai-compatible",
      "base_url": data["base_url"] if "base_url" in data else "",
      "api_path": data["api_path"] if "api_path" in data else "/v1",
      "api_key": data["api_key"] if "api_key" in data else None,
      "model_name": data["model_name"] if "model_name" in data else "",
      "headers_json": data["headers_json"] if "headers_json" in data else None,
      "options_json": data["options_json"] if "options_json" in data else None,
    })

    return {
      "success": True,
      "message": TAG_C001,
      "data": {
        "item": await _serialize_ai_model_endpoint(item),
      },
    }

  except HTTPException as e:
    raise e

  except HTTPException as e:
    raise e

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


@router.patch("/ai_model_endpoint")
async def ai_model_endpoint_update(
  request: Request,
  id: str,
):
  try:
    headers = request.headers
    user, access_token = await fetch_loggedin_user_info(headers=headers)

    ensure_can_manage_other_parties(user)

    item = await AIModelEndpoint.filter(
      id=id,
      is_disabled=False,
      is_deleted=False,
    ).first()

    if not item:
      raise HTTPException(status_code=404, detail="Model endpoint not found")

    data = await request.json()

    if "name" in data:
      item.name = data["name"]
    if "desc" in data:
      item.desc = data["desc"]
    if "model_type" in data:
      item.model_type = _normalize_model_type(data["model_type"])
    if "provider" in data:
      item.provider = data["provider"]
    if "base_url" in data:
      item.base_url = data["base_url"]
    if "api_path" in data:
      item.api_path = data["api_path"]
    if "api_key" in data:
      item.api_key = data["api_key"]
    if "model_name" in data:
      item.model_name = data["model_name"]
    if "headers_json" in data:
      item.headers_json = data["headers_json"]
    if "options_json" in data:
      item.options_json = data["options_json"]

    await item.save()

    return {
      "success": True,
      "message": TAG_C001,
      "data": {
        "item": await _serialize_ai_model_endpoint(item),
      },
    }

  except HTTPException as e:
    raise e

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


@router.delete("/ai_model_endpoint")
async def ai_model_endpoint_delete(
  request: Request,
  id: str,
):
  try:
    headers = request.headers
    user, access_token = await fetch_loggedin_user_info(headers=headers)

    ensure_can_manage_other_parties(user)

    item = await AIModelEndpoint.filter(
      id=id,
      is_disabled=False,
      is_deleted=False,
    ).first()

    if not item:
      raise HTTPException(status_code=404, detail="Model endpoint not found")

    item.is_deleted = True
    await item.save()

    await Party.filter(default_llm_model_id=item.id).update(default_llm_model_id=None)
    await Party.filter(default_embedding_model_id=item.id).update(default_embedding_model_id=None)

    return {
      "success": True,
      "message": TAG_C001,
      "data": {
        "item": await _serialize_ai_model_endpoint(item),
      },
    }

  except HTTPException as e:
    raise e

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


@router.post("/party/reembed_embeddings")
async def party_reembed_embeddings(
  request: Request,
  id: str,
):
  try:
    headers = request.headers
    user, access_token = await fetch_loggedin_user_info(headers=headers)

    ensure_can_manage_other_parties(user)

    item = await Party.filter(
      id=id,
      is_disabled=False,
      is_deleted=False,
    ).first()

    if not item:
      raise HTTPException(status_code=404, detail="Party not found")

    from src.controllers.functions.esbundle import es_chatllm as ESChatLLM

    result = await ESChatLLM.bot_es_reembed_index(index_name=str(item.id))

    return {
      "success": True,
      "message": TAG_C001,
      "data": {
        "item": await _serialize_party(item),
        "result": result,
      },
    }

  except HTTPException as e:
    raise e

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
    
    
    
    