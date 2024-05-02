from fastapi import FastAPI
from tortoise.contrib.fastapi import register_tortoise
from contextlib import asynccontextmanager


app = FastAPI(title="Tortoise ORM FastAPI example")

register_tortoise(
        app,
        db_url="sqlite://:memory:",
        modules={"models": ["models"]},
        generate_schemas=False,
        add_exception_handlers=True,
    )






import sys
import os

parent_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(parent_dir + "/../")

from controllers.apis.file import router as router_file
from controllers.apis.health import router as router_health


app.include_router(router = router_file)
app.include_router(router = router_health)

