

from fastapi import APIRouter, Request

from src.controllers.functions.rag.pglite_vector_store import PGliteVectorStore
from src.controllers.functions.user.setup import superadmin_exists

router = APIRouter(prefix="/api/v1")


@router.get("/setup/status")
async def get_setup_status():
    has_superadmin = await superadmin_exists()
    return {
      "success": True,
      "message": "C_SETUP_001",
      "data": {
        "setup_required": not has_superadmin,
        "superadmin_exists": has_superadmin,
      },
    }


@router.get("/health")
async def get_health(
  request: Request
):
    headers = request.headers
    pglite_health = {"ready": False}
    try:
      sidecar_health = await PGliteVectorStore().health()
      pglite_health = {
        "ready": sidecar_health.get("ready") == 1,
        "schema_version": sidecar_health.get("schema_version"),
      }
    except Exception:
      pass

    return {
      "success": True,
      "message": f"C_HEALTH_001",
      "data": {
        "service": "ready",
        "pglite": pglite_health,
      },
    }
