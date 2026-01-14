from fastapi import APIRouter, Query, Request

from app.core.decorators.auth_decorator import no_auth
from .data_load_repository import DataLoadRepository

router = APIRouter(prefix="/load", tags=["DataLoad"])
repository = DataLoadRepository()

@router.post("/upload_excel")
async def data_load(request: Request):
    return await repository.create_many(request)

@router.get("")
async def get_items(request: Request, parent_id: str | None = Query(default=None)):
    return await repository.get_items(request, parent_id)

@router.get("/read")
async def read(request: Request):
    return await repository.read(request)
    