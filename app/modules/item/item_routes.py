from bson import ObjectId
from fastapi import APIRouter, HTTPException, Request
from app.core.decorators.auth_decorator import no_auth
from app.modules.item.item_repository import ItemRepository

router = APIRouter(prefix="/item", tags=["Item"])
repository = ItemRepository()

@router.post("")
async def create(request: Request):
    return await repository.check_item(request)

@router.delete("/{object_id}")
async def destroy(
    object_id: str,
    request: Request,
):
    if not ObjectId.is_valid(object_id):
        raise HTTPException(status_code=400, detail="ObjectId inválido")

    deleted_count = await repository.destroy_cascade(
        request.state.db,
        ObjectId(object_id)
    )

    return {
        "status": "ok",
        "deleted_count": deleted_count
    }