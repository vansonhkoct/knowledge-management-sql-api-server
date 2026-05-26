import asyncio
import copy

from dotenv import load_dotenv
from tortoise import Tortoise

from database import TORTOISE_ORM
from src.controllers.functions.file_ingest.service import run_file_ingest_worker


load_dotenv(
  verbose=True,
  override=True,
)


async def main():
  dbConfig = copy.deepcopy(TORTOISE_ORM)
  dbConfig["apps"]["models"]["models"] = [
    "src.schemas.master",
    "aerich.models",
  ]
  dbConfig["apps"]["models"]["default_connection"] = "default"

  await Tortoise.init(config=dbConfig)
  try:
    await run_file_ingest_worker()
  finally:
    await Tortoise.close_connections()


if __name__ == '__main__':
  asyncio.run(main())