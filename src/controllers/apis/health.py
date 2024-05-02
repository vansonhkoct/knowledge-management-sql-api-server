

from fastapi import APIRouter, File, UploadFile

router = APIRouter(prefix="/api/v1")


@router.get("/health/")
async def get_health():
    return {
      "success": True,
      "message": f"C_HEALTH_001",
      "data": {

      },
    }

