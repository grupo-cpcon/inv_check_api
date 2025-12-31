from fastapi import APIRouter, File, Form, UploadFile
from .data_load_service import DataLoadService

router = APIRouter(prefix="/load", tags=["DataLoad"])
service = DataLoadService()

@router.post("/upload_excel")
async def data_load(file: UploadFile = File(...), extra_fields: str = Form(default="")):
    extra_fields_list = [f.strip() for f in extra_fields.split(',') if f.strip()]
    return await service.data_load(file, extra_fields_list)
    