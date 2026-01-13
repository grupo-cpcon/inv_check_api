import datetime
from bson import ObjectId
from fastapi import HTTPException, Request
from app.shared.storage.s3.objects import generate_s3_storage_object_key, storage_s3_save_object, storage_s3_retrieve_objects_url
from app.modules.item.item_storage_paths import ItemStoragePaths
from starlette.datastructures import UploadFile
import asyncio
from typing import List


class ItemRepository:
    async def check_status(
        request: Request,
        session_id: str,
        item_id: str
    ):
        db = request.state.db

        exists = await db.inventory_checks.find_one({
            "session_id": ObjectId(session_id),
            "item_id": ObjectId(item_id)
        })

        return {
            "checked": bool(exists)
        }

    async def check_item(self, request: Request):
        db = request.state.db
        form = await request.form()

        session_id: str = form.get("session_id")
        item_id: str = form.get("item_id")
        parent_id: str = form.get("parent_id")

        if not session_id or not item_id:
            raise HTTPException(400, "session_id, item_id e parent_id são obrigatórios")

        item = await db.inventory_items.find_one({"_id": ObjectId(item_id)})
        
        if not item:
            raise HTTPException(404, "Item não encontrado")

        exists = await db.inventory_checks.find_one({
            "session_id": ObjectId(session_id),
            "item_id": ObjectId(item_id)
        })

        if exists:
            raise HTTPException(400, "Item já inventariado")

        photos = form.getlist("photos") if "photos" in form else []
        base_item_photo_path = (
            ItemStoragePaths(
                client_name=request.state.db.name,
                session_id=ObjectId(session_id),
                item_id=ObjectId(item_id)
            ).images
        )
        photos_data = await self.perform_save_item_photos(photos, base_item_photo_path)
       
        doc = {
            "session_id": ObjectId(session_id),
            "item_id": ObjectId(item_id),
            "parent_id": ObjectId(parent_id),
            "checked": True,
            "checked_at": datetime.datetime.utcnow(),
            "photos": photos_data,
            "reference": item["reference"],
            # "asset_data": item["asset_data"],
            "path": item["path"]
        }

        await db.inventory_checks.insert_one(doc)

        return {
            "item_id": item_id,
            "parent_id": parent_id,
            "checked": True,
            "checked_at": datetime.datetime.utcnow(),
            "photos": await storage_s3_retrieve_objects_url(photos_data),
            "reference": item["reference"],
            # "asset_data": item["asset_data"],
            "path": item["path"]
        }

    async def perform_save_item_photos(self, photos: List[UploadFile], base_item_photo_path: str) -> List[str]:
        if not photos:
            return []

        def upload_task(photo):
            if not isinstance(photo, UploadFile):
                return None
            relative_save_path = generate_s3_storage_object_key(prefix=base_item_photo_path, file=photo)
            storage_s3_save_object(file=photo, relative_save_path=relative_save_path)
            return relative_save_path

        async_loop = asyncio.get_running_loop()
        tasks = [async_loop.run_in_executor(None, upload_task, photo) for photo in photos]
        results = await asyncio.gather(*tasks)
        return [result for result in results if result]