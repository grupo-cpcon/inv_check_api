from .data_load_repository import DataLoadRepository

class DataLoadService:
    def __init__(self):
        self.repository = DataLoadRepository()

    async def data_load(self, data: list[dict]):
        await self.repository.create_many(data)

