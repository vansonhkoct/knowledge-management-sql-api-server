
from fastapi import APIRouter

router = APIRouter()


@router.get("/api1/")
async def api1_endpoint():
    return {"message": "API 1 endpoint"}


@router.get("/api1/something")
async def api1_something():
    return {"message": "API 1 something"}
  
  