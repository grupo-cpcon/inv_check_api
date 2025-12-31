import json
from app.core.database import database

collection = database['items']

class ItemRepository:
    async def create(self, data: dict):
        result = await collection.insert_one(data)
        data["_id"] = str(result.inserted_id)
        return data

    async def create_many(self, data: list[dict]):
        results = await collection.insert_many(data)
        return {"ids": [str(_id) for _id in results.inserted_ids], "count": len(results.inserted_ids)}
    
    async def find_by(self, args: dict):
        cursor = collection.find(args)
        results = await cursor.to_list()
        
        for item in results:
            item["_id"] = str(item["_id"])
        return results
