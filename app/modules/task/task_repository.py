from fastapi import BackgroundTasks
import asyncio
import anyio
from typing import Dict, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.modules.task.task_schemas import (
    AsyncTaskCreateResponse,
    AsyncTaskCreateRequest,
)
from app.modules.task.task_choices import AsyncTaskStatus, AsyncTaskResultType, AsyncTaskType
from app.shared.storage.s3.objects import (
    generate_s3_storage_object_key,
    storage_s3_save_object,
)
from app.modules.task.task_storage_paths import TaskStoragePaths
from app.modules.task.task_factory import AsyncTaskFactory
from app.core.celery.tasks import celery_task
from app.shared.database.object_management import update_attributes


class AsyncTaskRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db["async_tasks"]

    async def create(
        self,
        task_type: AsyncTaskType,
        params: dict
    ):
        spec = AsyncTaskFactory.get_spec(task_type)
        task_doc = AsyncTaskCreateRequest(
            task_type=task_type.value,
            result_type=spec.result_type.value
        )

        result = await self.collection.insert_one(task_doc.model_dump())
        async_task_id = result.inserted_id

        try:
            celery_task.delay(
                task_id=str(async_task_id),
                task_type=task_type.value,
                db_name=self.db.name,
                params=params
            )
        except Exception as error:
            await update_attributes(
                collection=self.collection,
                object_id=async_task_id,
                status=AsyncTaskStatus.FAILED.value,
                log=str(error)
            )

        return AsyncTaskCreateResponse(
            _id=str(async_task_id),
            status=AsyncTaskStatus.PENDING.value
        )