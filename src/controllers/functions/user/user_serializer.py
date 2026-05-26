async def serialize_permission(permission):
  if permission is None:
    return None

  return {
    "id": str(permission.id),
    "name": permission.name,
    "desc": permission.desc,
    "code": permission.code,
    "is_disabled": permission.is_disabled,
    "is_deleted": permission.is_deleted,
  }


async def serialize_category(category):
  if category is None:
    return None

  return {
    "id": str(category.id),
    "name": category.name,
    "desc": category.desc,
    "alias": category.alias,
    "parent_category_id": str(category.parent_category_id) if category.parent_category_id else None,
    "party_id": str(category.party_id) if category.party_id else None,
    "is_disabled": category.is_disabled,
    "is_deleted": category.is_deleted,
  }


async def serialize_role(role):
  if role is None:
    return None

  await role.fetch_related("permissions", "accessible_categorys")

  return {
    "id": str(role.id),
    "name": role.name,
    "desc": role.desc,
    "code": role.code,
    "party_id": str(role.party_id) if role.party_id else None,
    "permissions": [await serialize_permission(item) for item in role.permissions],
    "accessible_categorys": [await serialize_category(item) for item in role.accessible_categorys],
    "is_disabled": role.is_disabled,
    "is_deleted": role.is_deleted,
  }


async def serialize_party(party):
  if party is None:
    return None

  return {
    "id": str(party.id),
    "name": party.name,
    "desc": party.desc,
    "default_llm_model_id": str(party.default_llm_model_id) if party.default_llm_model_id else None,
    "default_embedding_model_id": str(party.default_embedding_model_id) if party.default_embedding_model_id else None,
    "is_disabled": party.is_disabled,
    "is_deleted": party.is_deleted,
  }


async def serialize_user(user):
  if user is None:
    return None

  await user.fetch_related("party", "role")

  return {
    "id": str(user.id),
    "name": user.name,
    "desc": user.desc,
    "username": user.username,
    "email": user.email,
    "short_name": user.short_name,
    "phone_code": user.phone_code,
    "phone_number": user.phone_number,
    "party_id": str(user.party_id) if user.party_id else None,
    "role_id": str(user.role_id) if user.role_id else None,
    "party": await serialize_party(user.party),
    "role": await serialize_role(user.role),
    "is_disabled": user.is_disabled,
    "is_deleted": user.is_deleted,
  }