from app.core.database import database
from bson import ObjectId

collection = database["items"]

class ItemRepository:
    async def create(self, data: list[dict], parent_id: ObjectId | None = None):
        """ doc = {
            "name": data.get('name'),
            "parent_id": parent_id
        } """    
        result = await collection.insert_many(data)
        """ node_id = result.inserted_id
 """
        """ if data.get('children'):
            for child in data.get('children'):
                await self.create(child, node_id)
         """
        return str("")