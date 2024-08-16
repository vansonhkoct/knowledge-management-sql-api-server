

from fastapi import APIRouter, Request

from src.controllers.functions._generic.serverutils import get_memory_usage, get_cpu_usage, get_disk_usage
from src.controllers.functions._generic.fileutils import getStaticFilesBaseUrl, getUploadFilesBaseUrl

router = APIRouter(prefix="/api/v1")


@router.get("/health")
async def get_health(
  request: Request
):
    headers = request.headers

    return {
      "success": True,
      "message": f"C_HEALTH_001",
      "data": {
        "memory": get_memory_usage(),
        "cpy": get_cpu_usage(),
        "disk": get_disk_usage(),
        "staticFilesBaseUrl": getStaticFilesBaseUrl(),
        "uploadFilesBaseUrl": getUploadFilesBaseUrl(),
      },
    }

