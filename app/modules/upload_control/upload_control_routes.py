from app.modules.task.task_repository import AsyncTaskRepository
from fastapi import status
from app.modules.task.task_choices import AsyncTaskType

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Request
from typing import Optional
from app.modules.task.task_schemas import AsyncTaskCreateResponse
import base64
import zipfile
import io

router = APIRouter(prefix="/upload-control", tags=["Upload Control"])

@router.post(
    "/items-images", 
    response_model=AsyncTaskCreateResponse,
    status_code=status.HTTP_202_ACCEPTED
)
async def images_upload(
    request: Request, 
    file: UploadFile = File(media_type="application/zip")
) -> AsyncTaskCreateResponse:   

    try:
        content = await file.read()
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Erro ao ler o arquivo")

    if not zipfile.is_zipfile(io.BytesIO(content)):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Arquivo não é um ZIP válido")

    try:
        encoded_file = base64.b64encode(content).decode("utf-8")
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro ao processar arquivo")

    repository = AsyncTaskRepository(request.state.db)
    async_task = await repository.create(
        task_type=AsyncTaskType.UPLOAD_ITEMS_IMAGES,
        params={"encoded_file": encoded_file}
    )

    return async_task