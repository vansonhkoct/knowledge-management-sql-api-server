from dataclasses import asdict, dataclass

from fastapi import HTTPException


class PermissionCode:
  USER_MANAGE = "user.manage"
  FILE_MANAGE = "file.manage"
  FILE_INDEX = "file.index"
  ROLE_MANAGE = "role.manage"
  CATEGORY_MANAGE = "category.manage"
  CATEGORY_UPLOAD = "category.upload"
  KNOWLEDGE_SEARCH = "knowledge.search"
  PARTY_MANAGE = "party.manage"
  SHARED_CATEGORY_MANAGE = "shared_category.manage"


@dataclass(frozen=True)
class PermissionDefinition:
  code: str
  name: str
  description: str

  def serialize(self) -> dict:
    return asdict(self)


PERMISSION_DEFINITIONS = (
  PermissionDefinition(PermissionCode.USER_MANAGE, "Manage users", "Create, edit, and remove users."),
  PermissionDefinition(PermissionCode.FILE_MANAGE, "Manage files", "Upload, edit, and remove files."),
  PermissionDefinition(PermissionCode.FILE_INDEX, "Manage file indexing", "Queue files and inspect indexing jobs."),
  PermissionDefinition(PermissionCode.ROLE_MANAGE, "Manage roles", "Create roles and change role permissions."),
  PermissionDefinition(PermissionCode.CATEGORY_MANAGE, "Manage categories", "Create, edit, and remove categories."),
  PermissionDefinition(PermissionCode.CATEGORY_UPLOAD, "Upload to categories", "Upload content to accessible categories."),
  PermissionDefinition(PermissionCode.KNOWLEDGE_SEARCH, "Search knowledge", "Search and chat with indexed knowledge."),
  PermissionDefinition(PermissionCode.PARTY_MANAGE, "Manage organizations", "Manage all organizations and their settings."),
  PermissionDefinition(PermissionCode.SHARED_CATEGORY_MANAGE, "Manage shared categories", "Manage category sharing across organizations."),
)

PERMISSIONS_BY_CODE = {item.code: item for item in PERMISSION_DEFINITIONS}
ALL_PERMISSION_CODES = tuple(PERMISSIONS_BY_CODE)

LEGACY_PERMISSION_CODE_MAP = {
  "user -> manage": PermissionCode.USER_MANAGE,
  "file -> manage": PermissionCode.FILE_MANAGE,
  "admin -> manage_file_indexing": PermissionCode.FILE_INDEX,
  "role -> manage": PermissionCode.ROLE_MANAGE,
  "category -> manage": PermissionCode.CATEGORY_MANAGE,
  "category -> upload": PermissionCode.CATEGORY_UPLOAD,
  "knowledge -> search": PermissionCode.KNOWLEDGE_SEARCH,
  "superadmin -> manage_partys": PermissionCode.PARTY_MANAGE,
  "superadmin -> manage_shared_categorys": PermissionCode.SHARED_CATEGORY_MANAGE,
}


def normalize_permission_code(code: str) -> str:
  normalized = LEGACY_PERMISSION_CODE_MAP.get(code, code)
  if normalized not in PERMISSIONS_BY_CODE:
    raise ValueError(f"Unknown permission code: {code}")
  return normalized


def serialize_permission(code: str) -> dict:
  return PERMISSIONS_BY_CODE[normalize_permission_code(code)].serialize()


def ensure_permission(user, code: str):
  from src.controllers.functions.user.userscope import user_has_permission

  if not user_has_permission(user, normalize_permission_code(code)):
    raise HTTPException(status_code=403, detail="Permission denied")


async def assign_role_permissions(role, permission_codes):
  from src.models.master import RolePermissionAssignment

  normalized_codes = {normalize_permission_code(code) for code in permission_codes}
  existing_codes = set(await RolePermissionAssignment.filter(
    role_id=role.id,
    permission_code__in=normalized_codes,
  ).values_list("permission_code", flat=True))
  new_assignments = [
    RolePermissionAssignment(role_id=role.id, permission_code=code)
    for code in sorted(normalized_codes - existing_codes)
  ]
  if new_assignments:
    await RolePermissionAssignment.bulk_create(new_assignments)
