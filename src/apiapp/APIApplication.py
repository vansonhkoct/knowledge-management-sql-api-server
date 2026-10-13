import asyncio

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import copy
import os
from tortoise import Tortoise



from database import TORTOISE_ORM, should_generate_schemas

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
from src.controllers.apis.api_conversation import router as router_conversation
from src.controllers.apis.api_party_shared_categorys import router as router_party_shared_categorys
from src.controllers.apis.api_role_accessible_categorys import router as router_role_accessible_categorys
from src.controllers.apis.api_role_permission import router as router_role_permission
from src.controllers.functions.file_ingest.service import listen_for_file_status_events
from src.controllers.functions._generic.secretutils import migrate_legacy_ai_endpoint_secrets
from src.controllers.functions.ws.FileStatusConnectionManager import fileStatusConnectionManager


dbConfig = copy.deepcopy(TORTOISE_ORM)
dbConfig["apps"]["models"]["models"] = [
    "src.schemas.master",
    "aerich.models",
]
dbConfig["apps"]["models"]["default_connection"] = "default"

@asynccontextmanager
async def lifespan(app: FastAPI):
  await Tortoise.init(config=dbConfig)
  if should_generate_schemas():
    await Tortoise.generate_schemas(safe=True)
  await migrate_legacy_ai_endpoint_secrets()
  listener_task = asyncio.create_task(_relay_file_status_events())
  try:
    yield
  finally:
    listener_task.cancel()
    try:
      await listener_task
    except asyncio.CancelledError:
      pass
    await Tortoise.close_connections()


async def _relay_file_status_events():
  async def _handle_message(payload: dict):
    dict_payload = payload.get("dict") or {}
    party_id = dict_payload.get("party_id")
    if not party_id:
      return
    await fileStatusConnectionManager.broadcast_to_party(party_id, payload)

  await listen_for_file_status_events(_handle_message)


app = FastAPI(lifespan=lifespan)


def _sanitize_http_exception_detail(status_code: int, detail):
  if os.getenv("APP_ENV", "development").lower() != "production" or status_code < 500:
    return detail
  if isinstance(detail, dict):
    sanitized = {key: value for key, value in detail.items() if key != "stacktrace"}
    sanitized["error"] = "Internal server error"
    return sanitized
  return "Internal server error"


@app.exception_handler(HTTPException)
async def sanitized_http_exception_handler(request: Request, exception: HTTPException):
  return JSONResponse(
    status_code=exception.status_code,
    content={"detail": _sanitize_http_exception_detail(exception.status_code, exception.detail)},
    headers=exception.headers,
  )

app.add_middleware(
  CORSMiddleware,
  allow_origins=[
    origin.strip()
    for origin in os.getenv(
      "CORS_ALLOW_ORIGINS",
      "http://localhost:3000,http://localhost:5173",
    ).split(",")
    if origin.strip()
  ],
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"],
)

# Mount the static files directory
try:
  app.mount("/static", StaticFiles(directory="./static"), name="static")
except:
  pass

# Public upload serving is legacy-only. Production file access goes through the
# authenticated `/api/v1/file/content` endpoint.
if os.getenv("SERVE_PUBLIC_UPLOADS", "0") == "1":
  try:
    app.mount("/upload", StaticFiles(directory="./upload"), name="upload")
  except Exception:
    pass


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
app.include_router(router = router_conversation)
app.include_router(router = router_party_shared_categorys)
app.include_router(router = router_role_accessible_categorys)
app.include_router(router = router_role_permission)
