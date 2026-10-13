from src.models.master import User


async def superadmin_exists() -> bool:
  return await User.filter(
    is_disabled=False,
    is_deleted=False,
    role__code="superadmin",
    role__is_disabled=False,
    role__is_deleted=False,
  ).exists()
