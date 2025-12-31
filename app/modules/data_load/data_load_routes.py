from fastapi import APIRouter
from .data_load_service import DataLoadService

router = APIRouter(prefix="/load", tags=["DataLoad"])
service = DataLoadService()

@router.post("/", status_code=204)
async def data_load(data: list[dict]):
    await service.data_load(data)
