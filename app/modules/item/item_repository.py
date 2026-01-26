import datetime
from bson import ObjectId
from fastapi import HTTPException, Request
from app.shared.storage.s3.objects import generate_s3_storage_object_key, storage_s3_save_object, storage_s3_retrieve_objects_url
from app.modules.item.item_storage_paths import ItemStoragePaths
from starlette.datastructures import UploadFile
import asyncio
from typing import List
from motor.motor_asyncio import AsyncIOMotorDatabase


class ItemRepository:
    async def check_item(self, request: Request):
        db: AsyncIOMotorDatabase = request.state.db
        form = await request.form()

        item_id: str = form.get("item_id")
        
        item = await db.inventory_items.find_one({"_id": ObjectId(item_id)})
        
        if not item:
            raise HTTPException(404, "Item não encontrado")

        if item.get("checked"):
            raise HTTPException(400, "Item já inventariado")

        photos = form.getlist("photos") if "photos" in form else []
        base_item_photo_path = (
            ItemStoragePaths(
                client_name=request.state.db.name,
                item_id=ObjectId(item_id)
            ).images
        )
        photos_data = await self.perform_save_item_photos(photos, base_item_photo_path)
       
        doc = {
            "checked": True,
            "checked_at": datetime.datetime.utcnow(),
            "photos": photos_data,
        }

        await db.inventory_items.update_one(
            {"_id": ObjectId(item_id)},
            {"$set": doc})

        return {
            "id": item_id,
            "parent_id": str(item.get("parent_id")),
            "checked": True,
            "checked_at": datetime.datetime.utcnow(),
            "photos": await storage_s3_retrieve_objects_url(photos_data),
            "reference": item["reference"],
            "asset_data": item["asset_data"],
            "path": item["path"]
        }

    async def destroy_cascade(self, db: AsyncIOMotorDatabase, object_id: ObjectId):
        pipeline = [
            {"$match": {"_id": object_id}},
            {
                "$graphLookup": {
                    "from": "inventory_items",
                    "startWith": "$_id",
                    "connectFromField": "_id",
                    "connectToField": "parent_id",
                    "as": "descendants"
                }
            },
            {
                "$project": {
                    "items": {
                        "$concatArrays": [["$$ROOT"], "$descendants"]
                    }
                }
            },
            {"$unwind": "$items"},
            {
                "$project": {
                    "_id": "$items._id",
                    "reference": "$items.reference",
                    "path": "$items.path",
                    "node_type": "$items.node_type"
                }
            }
        ]

        cursor = db.inventory_items.aggregate(pipeline)
        docs = await cursor.to_list(length=None)
        ids_to_delete = [doc["_id"] for doc in docs]
        result = await db.inventory_items.delete_many({
            "_id": {"$in": ids_to_delete}
        })

        return result.deleted_count

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