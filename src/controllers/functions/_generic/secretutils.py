import base64
import hashlib
import os

from cryptography.fernet import Fernet, InvalidToken


SECRET_PREFIX = "enc:v1:"


def _get_cipher() -> Fernet:
  secret_key = os.getenv("AI_ENDPOINT_SECRET_KEY", "").strip()
  if not secret_key:
    raise RuntimeError(
      "AI_ENDPOINT_SECRET_KEY is required to store or use provider API keys"
    )

  derived_key = base64.urlsafe_b64encode(
    hashlib.sha256(secret_key.encode("utf-8")).digest()
  )
  return Fernet(derived_key)


def is_encrypted_secret(value: str | None) -> bool:
  return bool(value and value.startswith(SECRET_PREFIX))


def encrypt_secret(value: str | None) -> str | None:
  if value is None or value == "":
    return None
  if is_encrypted_secret(value):
    return value

  encrypted = _get_cipher().encrypt(value.encode("utf-8")).decode("ascii")
  return f"{SECRET_PREFIX}{encrypted}"


def decrypt_secret(value: str | None) -> str | None:
  if value is None or value == "":
    return None

  # Legacy plaintext values are accepted only so startup migration can encrypt
  # deployments upgraded from the earlier schema.
  if not is_encrypted_secret(value):
    return value

  token = value[len(SECRET_PREFIX):]
  try:
    return _get_cipher().decrypt(token.encode("ascii")).decode("utf-8")
  except InvalidToken as error:
    raise RuntimeError(
      "Unable to decrypt an AI endpoint API key; verify AI_ENDPOINT_SECRET_KEY"
    ) from error


async def migrate_legacy_ai_endpoint_secrets() -> int:
  from src.models.master import AIModelEndpoint

  legacy_items = await AIModelEndpoint.filter(api_key__not_isnull=True).exclude(api_key="")
  migrated_count = 0
  for item in legacy_items:
    if is_encrypted_secret(item.api_key):
      decrypt_secret(item.api_key)
      continue
    item.api_key = encrypt_secret(item.api_key)
    await item.save(update_fields=["api_key", "modified_at"])
    migrated_count += 1

  return migrated_count
