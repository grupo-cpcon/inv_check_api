from .item_repository import ItemRepository

class ItemService:
    def __init__(self):
        self.repository = ItemRepository()

    async def create_item(self, data: dict):
        return await self.repository.create(data)
