from fastapi import FastAPI
from tortoise.contrib.fastapi import register_tortoise
from contextlib import asynccontextmanager





import sys
import os
import copy


parent_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(parent_dir + "/../")

from database import TORTOISE_ORM


dbConfig = copy.deepcopy(TORTOISE_ORM)
dbConfig["apps"]["models"]["models"] = [
    "schemas.master",
    "aerich.models",
]
dbConfig["apps"]["models"]["default_connection"] = "default"

app = FastAPI()


register_tortoise(
        app,
        config=dbConfig,
        generate_schemas=False,
        add_exception_handlers=True,
    )



from controllers.apis.api_file import router as router_file
app.include_router(router = router_file)

from controllers.apis.api_health import router as router_health
app.include_router(router = router_health)

from controllers.apis.api_category import router as router_category
app.include_router(router = router_category)



