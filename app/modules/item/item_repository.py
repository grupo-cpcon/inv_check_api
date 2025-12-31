from fastapi import Request

class ItemRepository:
    async def create(self, request: Request):
        payload = request.body
        result = await request.state.db_client.insert_one(payload)
        payload["_id"] = str(result.inserted_id)
        return payload

    async def create_many(self, data: list[dict]):
        results = await collection.insert_many(data)
        return {"ids": [str(_id) for _id in results.inserted_ids], "count": len(results.inserted_ids)}
    
    async def find_by(self, args: dict):
        cursor = collection.find(args)
        results = await cursor.to_list()
        
        for item in results:
            item["_id"] = str(item["_id"])
        return results
