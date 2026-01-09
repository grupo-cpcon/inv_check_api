from fastapi import APIRouter, Request
from app.core.decorators.auth_decorator import no_auth
from app.modules.item.item_repository import ItemRepository

router = APIRouter(prefix="/item", tags=["Item"])
repository = ItemRepository()

@no_auth
@router.post("")
async def create(request: Request):
    return await repository.check_item(request)

@router.post("/status")
async def check_status(session_id: str, item_id: str, request: Request):
    return await repository.check_status(request, session_id, item_id)