import asyncio
import copy

from dotenv import load_dotenv
from tortoise import Tortoise

load_dotenv(
  verbose=True,
  override=True,
)

from database import TORTOISE_ORM, should_generate_schemas
from src.controllers.functions._generic.secretutils import migrate_legacy_ai_endpoint_secrets
from src.controllers.functions.file_ingest.service import run_file_ingest_worker


async def main():
  dbConfig = copy.deepcopy(TORTOISE_ORM)
  dbConfig["apps"]["models"]["models"] = [
    "src.schemas.master",
    "aerich.models",
  ]
  dbConfig["apps"]["models"]["default_connection"] = "default"

  await Tortoise.init(config=dbConfig)
  if should_generate_schemas():
    await Tortoise.generate_schemas(safe=True)
  await migrate_legacy_ai_endpoint_secrets()
  try:
    await run_file_ingest_worker()
  finally:
    await Tortoise.close_connections()


if __name__ == '__main__':
  try:
    asyncio.run(main())
  except KeyboardInterrupt:
    pass
