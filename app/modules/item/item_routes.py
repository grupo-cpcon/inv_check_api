from typing import Optional
from fastapi import APIRouter, Body, Query, Request
from app.modules.item.item_repository import ItemRepository

router = APIRouter(prefix="/item", tags=["Item"])
repository = ItemRepository()

# TODO: add service to check if has images. if yes send it to a bucket

@router.post("/")
async def create(payload: dict = Body(...)):
    return await repository.create(payload)

@router.post("/batch")
async def create_items_batch(data: list[dict] = Body(...)):
    return await repository.create_many(data)

@router.get("/")
async def get_items(request: Request):
    args = dict(request.query_params)
    return await repository.find_by(args)
