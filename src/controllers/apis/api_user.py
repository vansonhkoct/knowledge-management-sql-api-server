import traceback
from fastapi import APIRouter, File, UploadFile, Form, Request
from fastapi import HTTPException
from typing import Annotated
from tortoise.expressions import Q
from tortoise.contrib.pydantic import pydantic_model_creator

from src.controllers.functions.user.user import create_user, update_user_password
from src.controllers.functions.user.userauth_session import fetch_loggedin_user_info, delete_access_token

from src.models.master import KMUser, User, Role, Permission, UserCredential, UserCredentialType


router = APIRouter(prefix="/api/v1")


TAG_C001 = "C_USER001"
TAG_E001 = "E_USER001"




@router.get("/user/me")
async def user_me(
  request: Request,
):
  headers = request.headers
  user, access_token = await fetch_loggedin_user_info(headers=headers)

  # KMUser = pydantic_model_creator(
  #   User, 
  #   name="user", 
  #   # exclude=[
  #   #   "userCredentials",
  #   #   "userRequests",
  #   #   "userSessions",
  #   #   "party.roles",
  #   #   "chatMessages",
  #   # ]
  # )
  
  item = await KMUser.from_tortoise_orm(user)

  try:
    return {
      "success": True,
      "message": TAG_C001,
      "data": {
        "item": item,
      }
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



@router.post("/user/logout")
async def user_logout(
  request: Request,
):
  headers = request.headers
  user, access_token = await fetch_loggedin_user_info(headers=headers)

  try:
    await delete_access_token(access_token=access_token)
    
    return {
      "success": True,
      "message": TAG_C001,
      "data": {
        "item": user,
      }
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










@router.post("/user")
async def user_create(
  request: Request,
):
  try:
    headers = request.headers
    user, access_token = await fetch_loggedin_user_info(headers=headers)

    data = await request.json()

    role_id = data["role_id"] if "role_id" in data else None
    role = await Role.filter(id=role_id).first()

    name = data["name"] if "name" in data else None
    username = data["username"] if "username" in data else ""
    password = data["password"] if "password" in data else ""
    
    item = await create_user(
      name=name,
      party_id=user.party_id,
      role_id=role_id,
      username=username,
      password=password,
    )
    
    return {
      "success": True,
      "message": TAG_C001,
      "data": {
        "item": item,
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




@router.get("/user")
async def fetch(
  request: Request,
  page: int = 0,
  limit: int = 10,
):
  try:
    headers = request.headers
    user, access_token = await fetch_loggedin_user_info(headers=headers)
    
    # Calculate the offset based on the page and limit
    offset = (page) * limit
    
    # Fetch the category items from the database using Tortoise ORM
    filters = {}
    filters["party_id"] = user.party_id if user != None else None
    filters["is_disabled"] = False
    filters["is_deleted"] = False

    items = (
      await User
        .filter(Q(**filters))
        .offset(offset)
        .limit(limit)
    )
    
    total_count = (
      await User
        .filter(Q(**filters))
        .count()
    )

    tsql = (
      User
        .filter(Q(**filters))
        .sql()
    )

    for k in range(len(items)):
      items[k] = await KMUser.from_tortoise_orm(items[k]) 

    return {
      "success": True,
      "message": TAG_C001,
      "data": {
        "filters": filters,
        "sql": tsql,
        "pagination": {
          "page": page,
          "limit": limit,
          "total_count": total_count,
        },
        "items": items,
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







@router.get("/user/single")
async def fetchSingle(
  request: Request,
  id: str,
):
  try:
    headers = request.headers
    user, access_token = await fetch_loggedin_user_info(headers=headers)
    
    filters = {}
    filters["id"] = id
    filters["party_id"] = user.party_id if user != None else None
    filters["is_disabled"] = False
    filters["is_deleted"] = False

    item = (
      await User
        .filter(Q(**filters))
        .first()
    )
    

    return {
      "success": True,
      "message": TAG_C001,
      "data": item,
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




@router.patch("/user")
async def update(
  request: Request,
  id: str,
):
  try:
    headers = request.headers
    user, access_token = await fetch_loggedin_user_info(headers=headers)
  
    filters = {}
    filters["party_id"] = user.party_id if user != None else None
    filters["id"] = id

    item = (
      await User
        .filter(Q(**filters))
        .first()
    )
    
    if not item:
      raise HTTPException(status_code=404, detail="User not found")
    
    
    
    data = await request.json()


    if "name" in data:
      item.name = data["name"]

    if "role_id" in data:
      item.role_id = data["role_id"]

    if "username" in data:
      item.username = data["username"]


    await item.save()


    if "password" in data:
      await update_user_password(
        user_id=item.id,
        password=data["password"],
      )
    
    
    
    return {
      "success": True,
      "message": TAG_C001,
      "data": {
        "item": item,
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
    
    




@router.delete("/user")
async def remove(
  request: Request,
  id: str,
):
  try:
    headers = request.headers
    user, access_token = await fetch_loggedin_user_info(headers=headers)
  
    filters = {}
    filters["party_id"] = user.party_id if user != None else None
    filters["id"] = id

    item = (
      await User
        .filter(Q(**filters))
        .first()
    )
    
    if not item:
      raise HTTPException(status_code=404, detail="User not found")

    item.name = f"Deleted user ({item.name})"
    item.is_deleted = True
    await item.save()

    userCredentials = await item.userCredentials.all()
    for it in userCredentials:
      it.is_deleted = True
      await it.save()

    userSessions = await item.userSessions.all()
    for it in userSessions:
      it.is_deleted = True
      await it.save()
    
    return {
      "success": True,
      "message": TAG_C001,
      "data": {
        "item": item,
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
    