from fastapi import APIRouter, Request, UploadFile
from .data_load_service import DataLoadService

router = APIRouter(prefix="/load", tags=["DataLoad"])
service = DataLoadService()

@router.post("/upload_excel")
async def data_load(request: Request):
    return await service.data_load(request)
    