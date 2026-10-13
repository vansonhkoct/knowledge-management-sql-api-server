from fastapi import HTTPException

from src.controllers.functions.user.permissions import PermissionCode, normalize_permission_code


def normalize_scope_id(value):
  if value in [None, ""]:
    return None
  return str(value)


def get_user_permission_codes(user):
  role = getattr(user, "role", None)
  assignments = getattr(role, "permission_assignments", []) if role is not None else []
  return {
    assignment.permission_code: 1
    for assignment in assignments
    if assignment is not None and getattr(assignment, "permission_code", None)
  }


def user_has_permission(user, code: str):
  try:
    code = normalize_permission_code(code)
  except ValueError:
    return False
  return get_user_permission_codes(user).get(code) == 1


def can_manage_other_parties(user):
  return user_has_permission(user, PermissionCode.PARTY_MANAGE)


def ensure_can_manage_other_parties(user):
  if not can_manage_other_parties(user):
    raise HTTPException(status_code=403, detail="Permission denied")


def resolve_target_party_id(user, requested_party_id: str = None):
  current_party_id = normalize_scope_id(getattr(user, "party_id", None))
  requested_party_id = normalize_scope_id(requested_party_id)

  if requested_party_id in [None, ""]:
    return current_party_id

  if requested_party_id == current_party_id:
    return requested_party_id

  ensure_can_manage_other_parties(user)
  return requested_party_id
