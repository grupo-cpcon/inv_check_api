import datetime
from bson import ObjectId
from fastapi import HTTPException, Request
from app.shared.storage.s3.objects import generate_s3_storage_object_key, storage_s3_save_object, storage_s3_retrieve_objects_url
from app.modules.item.item_storage_paths import ItemStoragePaths
from starlette.datastructures import UploadFile
import asyncio
from typing import List
from motor.motor_asyncio import AsyncIOMotorDatabase
import json


class ItemRepository:
    async def check_item(self, request: Request):
        db: AsyncIOMotorDatabase = request.state.db
        form = await request.form()

        item_id: str = form.get("item_id")
        
        if not item_id:
            return await self.create_item(request, form)
        
        item = await db.inventory_items.find_one({"_id": ObjectId(item_id)})
        
        if not item:
            raise HTTPException(404, "Item não encontrado")

        # if item.get("checked"):
        #     raise HTTPException(400, "Item já inventariado")

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

        asset_data_str = form.get("asset_data")
        if asset_data_str:
            try:
                asset_data = json.loads(asset_data_str)
                doc["asset_data"] = asset_data
            except json.JSONDecodeError:
                pass

        new_parent_id_str = form.get("parent_id")
        new_path = item["path"]
        if new_parent_id_str:
            new_parent_id = ObjectId(new_parent_id_str)
            
            if new_parent_id != item.get("parent_id"):
                new_parent = await db.inventory_items.find_one({"_id": new_parent_id})
                if not new_parent:
                    raise HTTPException(400, "Item pai não encontrado")
                
                new_level = new_parent.get("level", 0) + 1
                new_path = new_parent.get("path", []) + [item["reference"]]
                
                doc["parent_id"] = new_parent_id
                doc["level"] = new_level
                doc["path"] = new_path

        await db.inventory_items.update_one(
            {"_id": ObjectId(item_id)},
            {"$set": doc})

        return {
            "id": item_id,
            "parent_id": str(doc.get("parent_id", item.get("parent_id"))),
            "checked": True,
            "checked_at": datetime.datetime.utcnow(),
            "photos": await storage_s3_retrieve_objects_url(photos_data),
            "reference": item["reference"],
            "asset_data": doc.get("asset_data", item.get("asset_data")),
            "path": new_path
        }
    
    async def create_item(self, request: Request, form):
        db: AsyncIOMotorDatabase = request.state.db
        
        reference = form.get("reference")
        parent_id_str = form.get("parent_id")
        
        if not reference:
            raise HTTPException(400, "Referência é obrigatória")
        
        if not parent_id_str:
            raise HTTPException(400, "Item pai é obrigatório")
        
        parent_id = ObjectId(parent_id_str)
        parent_item = await db.inventory_items.find_one({"_id": parent_id})
        if not parent_item:
            raise HTTPException(400, "Item pai não encontrado")
        
        root_reference = parent_item.get("path", [])[0] if parent_item.get("path") else None
        
        if root_reference:
            root_node = await db.inventory_items.find_one({
                "reference": root_reference,
                "parent_id": None
            })
        else:
            root_node = parent_item
            while root_node and root_node.get("parent_id") is not None:
                root_node = await db.inventory_items.find_one({"_id": root_node["parent_id"]})
        
        if not root_node:
            raise HTTPException(500, "Não foi possível encontrar a localização raiz")
        
        existing_item = await db.inventory_items.find_one({
            "reference": reference,
            "path.0": root_node["reference"]
        })
        
        if existing_item:
            raise HTTPException(
                400, 
                f"Já existe um item com a referência '{reference}' nesta árvore"
            )
        
        level = parent_item.get("level", 0) + 1
        path = parent_item.get("path", []) + [reference]
        
        item_id = ObjectId()
        
        photos = form.getlist("photos") if "photos" in form else []
        photos_data = []
        if photos:
            base_item_photo_path = ItemStoragePaths(
                client_name=db.name,
                item_id=item_id
            ).images
            photos_data = await self.perform_save_item_photos(photos, base_item_photo_path)
        
        asset_data = None
        asset_data_str = form.get("asset_data")
        if asset_data_str:
            try:
                asset_data = json.loads(asset_data_str)
            except json.JSONDecodeError:
                
                pass
        
        doc = {
            "_id": item_id,
            "reference": reference,
            "node_type": "ASSET",
            "parent_id": parent_id,
            "level": level,
            "checked": True,
            "checked_at": datetime.datetime.utcnow(),
            "path": path,
            "photos": photos_data,
        }
        
        if asset_data:
            doc["asset_data"] = asset_data
        
        await db.inventory_items.insert_one(doc)
        
        return {
            "id": str(item_id),
            "parent_id": str(parent_id) if parent_id else None,
            "reference": reference,
            "checked": True,
            "checked_at": datetime.datetime.utcnow(),
            "photos": await storage_s3_retrieve_objects_url(photos_data),
            "asset_data": asset_data,
            "path": path,
            "level": level
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