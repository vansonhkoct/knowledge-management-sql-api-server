from fastapi import HTTPException


def get_user_permission_codes(user):
  role = getattr(user, "role", None)
  permissions = getattr(role, "permissions", []) if role is not None else []
  return {
    it.code: 1
    for it in permissions
    if it is not None and getattr(it, "code", None)
  }


def user_has_permission(user, code: str):
  return (get_user_permission_codes(user)).get(code) == 1


def can_manage_other_parties(user):
  return user_has_permission(user, "superadmin -> manage_partys")


def ensure_can_manage_other_parties(user):
  if not can_manage_other_parties(user):
    raise HTTPException(status_code=403, detail="Permission denied")


def resolve_target_party_id(user, requested_party_id: str = None):
  current_party_id = getattr(user, "party_id", None)

  if requested_party_id in [None, ""]:
    return current_party_id

  if requested_party_id == current_party_id:
    return requested_party_id

  ensure_can_manage_other_parties(user)
  return requested_party_id