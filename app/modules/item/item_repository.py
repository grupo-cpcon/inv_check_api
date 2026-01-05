from fastapi import Request

class ItemRepository:
    async def create(self, payload: dict, request: Request):
        db = request.state.db
        result = await db.items.insert_one(payload)
        payload["_id"] = str(result.inserted_id)
        return payload

    async def create_many(self, data: list[dict], request: Request):
        db = request.state.db
        results = await db.items.insert_many(data)
        return {"ids": [str(_id) for _id in results.inserted_ids], "count": len(results.inserted_ids)}
    
    async def find_by(self, request: Request):
        db = request.state.db
        args: dict = request.query_params
        cursor = db.items.find(args)
        results = await cursor.to_list()
        
        for item in results:
            item["_id"] = str(item["_id"])
        return results
