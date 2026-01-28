import asyncio
import anyio
from abc import ABC, abstractmethod
from app.modules.task.task_choices import AsyncTaskStatus, AsyncTaskResultType
from typing import Any, Dict
from app.modules.task.task_storage_paths import TaskStoragePaths
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.shared.database.object_management import update_attributes

from app.shared.storage.s3.objects import (
    generate_s3_storage_object_key,
    storage_s3_save_object,
)


class BaseAsyncTaskHandler(ABC):
    def __init__(self, *, task_id: str, db: AsyncIOMotorDatabase, result_type: AsyncTaskResultType):
        self.task_id = task_id
        self.db = db
        self.collection = db["async_tasks"]
        self.result_type = result_type

    async def run(self, params: dict) -> None:
        try:
            await self.update_attributes(
                status=AsyncTaskStatus.IN_PROGRESS.value,
                progress=5
            )

            result = await self.execute(params)
            await self.update_attributes(
                progress=70
            )
            
            result = await self._handle_result(result)
            await self.update_attributes(
                status=AsyncTaskStatus.COMPLETED.value,
                progress=100,
                result=result
            )

        except Exception as exc:
            await self.update_attributes(
                status=AsyncTaskStatus.FAILED.value,
                log=str(exc),
            )
            raise

    async def update_attributes(self, **args):
        await update_attributes(
            collection=self.collection,
            object_id=self._oid,
            **args
        )

    async def _handle_result(self, result: Any) -> str:
        if self.result_type != AsyncTaskResultType.ARCHIVE:
            return result

        base_path = TaskStoragePaths(self.db.name).async_task(self.task_id)
        key = generate_s3_storage_object_key(prefix=base_path, file=result)

        await anyio.to_thread.run_sync(
            storage_s3_save_object,
            result,
            key
        )

        return key

    @property
    def _oid(self) -> ObjectId:
        return ObjectId(self.task_id)

    @abstractmethod
    async def execute(self, params: dict) -> Any:
        pass