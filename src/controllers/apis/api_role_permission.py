from fastapi import APIRouter, HTTPException, Request
from tortoise.transactions import atomic

from src.controllers.functions.user.permissions import (
  PermissionCode,
  ensure_permission,
  normalize_permission_code,
  serialize_permission,
)
from src.controllers.functions.user.userauth_session import fetch_loggedin_user_info
from src.controllers.functions.user.userscope import resolve_target_party_id
from src.models.master import Role, RolePermissionAssignment


router = APIRouter(prefix="/api/v1")

TAG_C001 = "C_ROLE_PERMISSION001"


def _serialize_role(item: Role) -> dict:
  return {
    "id": str(item.id),
    "party_id": str(item.party_id) if item.party_id else None,
    "code": item.code,
    "name": item.name,
    "desc": item.desc,
  }


async def _authorized_party(request: Request, requested_party_id: str | None):
  user, _ = await fetch_loggedin_user_info(headers=request.headers)
  ensure_permission(user, PermissionCode.ROLE_MANAGE)
  return resolve_target_party_id(user=user, requested_party_id=requested_party_id)


@router.get("/role_permissions/role_permissions")
async def fetch_role_permissions(
  request: Request,
  page: int = 0,
  limit: int = 100,
  role_id: str | None = None,
  party_id: str | None = None,
):
  target_party_id = await _authorized_party(request, party_id)
  role = await Role.filter(
    id=role_id,
    party_id=target_party_id,
    is_disabled=False,
    is_deleted=False,
  ).first()
  if role is None:
    raise HTTPException(status_code=404, detail="Role not found")

  codes = await RolePermissionAssignment.filter(role_id=role.id).order_by(
    "permission_code"
  ).values_list("permission_code", flat=True)
  items = [serialize_permission(code) for code in codes]
  offset = max(page, 0) * max(limit, 0)
  paginated_items = items[offset:offset + limit] if limit > 0 else []
  return {
    "success": True,
    "message": TAG_C001,
    "data": {
      "pagination": {"page": page, "limit": limit, "total_count": len(items)},
      "items": paginated_items,
    },
  }


@router.get("/role_permissions/permission_roles")
async def fetch_permission_roles(
  request: Request,
  page: int = 0,
  limit: int = 100,
  permission_code: str | None = None,
  party_id: str | None = None,
):
  target_party_id = await _authorized_party(request, party_id)
  try:
    permission_code = normalize_permission_code(permission_code) if permission_code else None
  except ValueError as error:
    raise HTTPException(status_code=400, detail=str(error)) from error
  filters = {
    "party_id": target_party_id,
    "is_disabled": False,
    "is_deleted": False,
  }
  if permission_code:
    filters["permission_assignments__permission_code"] = permission_code
  query = Role.filter(**filters).distinct()
  total_count = await query.count()
  items = await query.order_by("created_at").offset(page * limit).limit(limit)
  return {
    "success": True,
    "message": TAG_C001,
    "data": {
      "pagination": {"page": page, "limit": limit, "total_count": total_count},
      "items": [_serialize_role(item) for item in items],
    },
  }


@router.post("/role_permissions/bulk_update")
@atomic()
async def bulk_update_mappings(request: Request):
  data = await request.json()
  target_party_id = await _authorized_party(request, data.get("party_id"))
  add_mappings = data.get("add_mappings") or []
  remove_mappings = data.get("remove_mappings") or []

  async def resolve_mapping(mapping: dict):
    role = await Role.filter(
      id=mapping.get("role_id"),
      party_id=target_party_id,
      is_disabled=False,
      is_deleted=False,
    ).first()
    if role is None:
      raise HTTPException(status_code=404, detail="Role not found")
    try:
      permission_code = normalize_permission_code(mapping.get("permission_code"))
    except ValueError as error:
      raise HTTPException(status_code=400, detail=str(error)) from error
    return role, permission_code

  for mapping in add_mappings:
    role, permission_code = await resolve_mapping(mapping)
    await RolePermissionAssignment.get_or_create(
      role_id=role.id,
      permission_code=permission_code,
    )

  for mapping in remove_mappings:
    role, permission_code = await resolve_mapping(mapping)
    await RolePermissionAssignment.filter(
      role_id=role.id,
      permission_code=permission_code,
    ).delete()

  return {
    "success": True,
    "message": TAG_C001,
    "data": {
      "add_mappings": add_mappings,
      "remove_mappings": remove_mappings,
    },
  }
