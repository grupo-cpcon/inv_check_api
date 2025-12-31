from app.core.database import get_database


class ItemRepository:
    def __init__(self):
        self.collection = get_database()["items"]

    async def create(self, data: dict):
        result = await self.collection.insert_one(data)
        return str(result.inserted_id)

    async def list(self):
        users = []
        async for doc in self.collection.find():
            doc["_id"] = str(doc["_id"])
            users.append(doc)
        return users