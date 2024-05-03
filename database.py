TORTOISE_ORM = {
  "connections": {
      "default": "mysql://root:password@octopus-tech.com:16884/ai_knowledge_base_rag_db_2",
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
