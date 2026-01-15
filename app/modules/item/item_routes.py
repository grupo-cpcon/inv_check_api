from fastapi import APIRouter, Request
from app.core.decorators.auth_decorator import no_auth
from app.modules.item.item_repository import ItemRepository

router = APIRouter(prefix="/item", tags=["Item"])
repository = ItemRepository()

@router.post("")
async def create(request: Request):
    return await repository.check_item(request)