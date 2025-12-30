from app.core.database import database

collection = database["items"]

class ItemRepository:
    async def create(self, data: dict):
        result = await collection.insert_one(data)
        return str(result.inserted_id)