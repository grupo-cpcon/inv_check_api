from app.core.database import database

collection = database["data_loads"]

class DataLoadRepository:
    async def create_many(self, data: list[dict]):
        result = await collection.insert_many(data)
        return str(result)