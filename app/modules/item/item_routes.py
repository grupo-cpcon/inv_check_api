from fastapi import APIRouter, Request
from app.modules.item.item_repository import ItemRepository

router = APIRouter(prefix="/item", tags=["Item"])
repository = ItemRepository()

# TODO: add service to check if has images. if yes send it to a bucket

@router.post("/")
async def create(payload: dict, request: Request):
    return await repository.create(payload, request)

@router.post("/batch")
async def create_items_batch(data: list[dict], request: Request):
    return await repository.create_many(data, request)

@router.get("/")
async def get_items(request: Request):
    return await repository.find_by(request)
