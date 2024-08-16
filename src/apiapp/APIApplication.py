from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from tortoise.contrib.fastapi import register_tortoise
from contextlib import asynccontextmanager
import copy



from database import TORTOISE_ORM

from src.controllers.apis.api_ws import router as router_ws
from src.controllers.apis.api_file import router as router_file
from src.controllers.apis.api_file_estest import router as router_file_estest
from src.controllers.apis.api_health import router as router_health
from src.controllers.apis.api_category import router as router_category
from src.controllers.apis.api_user import router as router_user
from src.controllers.apis.api_role import router as router_role
from src.controllers.apis.api_permission import router as router_permission
from src.controllers.apis.api_party import router as router_party
from src.controllers.apis.api_auth import router as router_auth
from src.controllers.apis.api_party_shared_categorys import router as router_party_shared_categorys
from src.controllers.apis.api_role_accessible_categorys import router as router_role_accessible_categorys
from src.controllers.apis.api_role_permission import router as router_role_permission


dbConfig = copy.deepcopy(TORTOISE_ORM)
dbConfig["apps"]["models"]["models"] = [
    "src.schemas.master",
    "aerich.models",
]
dbConfig["apps"]["models"]["default_connection"] = "default"

app = FastAPI()

app.add_middleware(
  CORSMiddleware,
  allow_origins=["*"],
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"],
)

# Mount the static files directory
try:
  app.mount("/static", StaticFiles(directory="./static"), name="static")
except:
  pass

# Mount the upload files directory
try:
  app.mount("/upload", StaticFiles(directory="./upload"), name="upload")
except:
  pass


register_tortoise(
        app,
        config=dbConfig,
        generate_schemas=False,
        add_exception_handlers=True,
    )

app.include_router(router = router_ws)
app.include_router(router = router_file)
app.include_router(router = router_file_estest)
app.include_router(router = router_health)
app.include_router(router = router_category)
app.include_router(router = router_user)
app.include_router(router = router_role)
app.include_router(router = router_permission)
app.include_router(router = router_party)
app.include_router(router = router_auth)
app.include_router(router = router_party_shared_categorys)
app.include_router(router = router_role_accessible_categorys)
app.include_router(router = router_role_permission)




