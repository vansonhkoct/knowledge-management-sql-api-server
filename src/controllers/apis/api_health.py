

from fastapi import APIRouter, File, UploadFile, Request

router = APIRouter(prefix="/api/v1")


@router.get("/health/")
async def get_health(
  request: Request
):
    headers = request.headers
    form_data = request.form

    return {
      "success": True,
      "message": f"C_HEALTH_001",
      "data": {

      },
    }

