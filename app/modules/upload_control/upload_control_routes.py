from app.modules.task.task_repository import AsyncTaskRepository
from fastapi import status
from app.modules.task.task_choices import AsyncTaskType

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Request
from typing import Optional
from app.modules.task.task_schemas import AsyncTaskCreateResponse
import base64


router = APIRouter(prefix="/upload-control", tags=["Upload Control"])

@router.post(
    "/items-images", 
    response_model=AsyncTaskCreateResponse,
    status_code=status.HTTP_202_ACCEPTED
)
async def images_export(
    request: Request, 
    file: UploadFile = File(media_type="application/zip")
) -> AsyncTaskCreateResponse:   

    if not file.filename.endswith(".zip"):
        raise HTTPException(status_code=400, detail="Arquivo deve ser .zip")
    
    content = await file.read()
    encoded_file = base64.b64encode(content).decode("utf-8")

    repository = AsyncTaskRepository(request.state.db)
    async_task = await repository.create(
        task_type=AsyncTaskType.UPLOAD_ITEMS_IMAGES,
        params={"encoded_file": encoded_file}
    )

    return async_task