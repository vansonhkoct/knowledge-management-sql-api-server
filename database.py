import os
from pathlib import Path


APP_ENV = os.getenv("APP_ENV", "development").strip().lower()


def _resolve_database_url() -> str:
  database_url = (
    os.getenv("APP_DATABASE_URL")
    or os.getenv("MYSQL_CONNECTOR_STRING")
    or ""
  ).strip()

  if not database_url:
    if APP_ENV == "production":
      raise RuntimeError(
        "APP_DATABASE_URL or MYSQL_CONNECTOR_STRING is required in production"
      )
    database_url = "sqlite://var/dev/knowledge_management.sqlite3"

  if APP_ENV == "production" and database_url.startswith("sqlite://"):
    raise RuntimeError("SQLite is for development and tests only; configure MySQL in production")

  if database_url.startswith("sqlite://"):
    sqlite_path = database_url.removeprefix("sqlite://")
    if sqlite_path not in ["", ":memory:"]:
      Path(sqlite_path).expanduser().parent.mkdir(parents=True, exist_ok=True)

  return database_url


DATABASE_URL = _resolve_database_url()
IS_SQLITE = DATABASE_URL.startswith("sqlite://")


def should_generate_schemas() -> bool:
  # Production schema changes must always go through reviewed migrations.  This
  # guard deliberately wins over a stale or copied development environment flag.
  if APP_ENV == "production":
    return False

  configured = os.getenv("DATABASE_GENERATE_SCHEMAS")
  if configured is not None:
    return configured.strip().lower() in ["1", "true", "yes", "on"]
  return IS_SQLITE and APP_ENV in ["development", "test"]

TORTOISE_ORM = {
  "connections": {
      "default": DATABASE_URL,
  },
  "apps": {
      "models": {
          "models": [
            "src.schemas.master",
            "aerich.models",
          ],
          "default_connection": "default",
      }
  },
  "use_tz": False,
  "timezone": "UTC",
}
