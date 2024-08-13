import os

TORTOISE_ORM = {
  "connections": {
      "default": os.getenv("MYSQL_CONNECTOR_STRING"),
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
