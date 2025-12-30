from fastapi import APIRouter, HTTPException
from .item_service import ItemService
from typing import List

router = APIRouter(prefix="/items", tags=["Items"])
service = ItemService()

@router.post("/", response_model=str)
async def create_item(item: dict):
    return await service.create_item(item)
