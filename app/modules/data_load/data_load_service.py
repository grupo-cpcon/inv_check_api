from typing import List
from fastapi import File, UploadFile
from .data_load_repository import DataLoadRepository

class DataLoadService:
    def __init__(self):
        self.repository = DataLoadRepository()

    async def data_load(self, file: UploadFile = File(...), extra_fields: List[str] = []):
        return await self.repository.create_many(file, extra_fields)