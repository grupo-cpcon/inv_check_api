from fastapi import APIRouter, Request, UploadFile

from app.core.decorators.auth_decorator import no_auth
from .data_load_service import DataLoadService

router = APIRouter(prefix="/load", tags=["DataLoad"])
service = DataLoadService()

@router.post("/upload_excel")
async def data_load(request: Request):
    return await service.data_load(request)

@no_auth
@router.get("/read")
async def data_load(request: Request):
    return await service.read(request)
    