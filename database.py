TORTOISE_ORM = {
  "connections": {
      "default": "mysql://root:password@192.168.2.107:16884/ai_knowledge_base_rag_db_2",
  },
  "apps": {
      "models": {
          "models": [
            "src.models.km_models",
            "aerich.models",
          ],
          "default_connection": "default",
      }
  },
  "use_tz": False,
  "timezone": "UTC",
}