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
            await self._set_status(
                AsyncTaskStatus.IN_PROGRESS
            )

            result = await self.execute(params)
            await update_attributes(
                collection=self.collection,
                object_id=self.task_id,
                progress=50
            )
            result = await self._handle_result(result)
            await update_attributes(
                collection=self.collection,
                object_id=self.task_id,
                progress=99
            )

            await self._set_status(
                AsyncTaskStatus.COMPLETED,
                progress=100,
                result=result
            )

        except Exception as exc:
            await self._set_status(
                AsyncTaskStatus.FAILED,
                error=str(exc),
            )
            raise

    async def _set_status(self, status: AsyncTaskStatus, **extra: Dict[Any, Any]) -> None:
        await self.collection.update_one(
            {"_id": self._oid()},
            {"$set": {"status": status.value, **extra}},
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

    def _oid(self) -> ObjectId:
        return ObjectId(self.task_id)

    @abstractmethod
    async def execute(self, params: dict) -> Any:
        pass