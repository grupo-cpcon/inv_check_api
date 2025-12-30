from .item_repository import ItemRepository

class ItemService:
    def __init__(self):
        self.repository = ItemRepository()

    async def create_item(self, item: list[dict]):
        return await self.repository.create(item)

