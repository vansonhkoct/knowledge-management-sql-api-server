from fastapi import APIRouter, HTTPException, Request

from src.controllers.functions.user.permissions import (
  PERMISSION_DEFINITIONS,
  PERMISSIONS_BY_CODE,
)
from src.controllers.functions.user.userauth_session import fetch_loggedin_user_info


router = APIRouter(prefix="/api/v1")

TAG_C001 = "C_PERMISSION001"


@router.get("/permission")
async def fetch_permissions(
  request: Request,
  page: int = 0,
  limit: int = 100,
):
  await fetch_loggedin_user_info(headers=request.headers)
  offset = max(page, 0) * max(limit, 0)
  items = [item.serialize() for item in PERMISSION_DEFINITIONS]
  paginated_items = items[offset:offset + limit] if limit > 0 else []
  return {
    "success": True,
    "message": TAG_C001,
    "data": {
      "pagination": {
        "page": page,
        "limit": limit,
        "total_count": len(items),
      },
      "items": paginated_items,
    },
  }


@router.get("/permission/single")
async def fetch_permission(
  request: Request,
  code: str,
):
  await fetch_loggedin_user_info(headers=request.headers)
  item = PERMISSIONS_BY_CODE.get(code)
  if item is None:
    raise HTTPException(status_code=404, detail="Permission not found")
  return {
    "success": True,
    "message": TAG_C001,
    "data": item.serialize(),
  }
