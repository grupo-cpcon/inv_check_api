from fastapi import BackgroundTasks
import asyncio
import uuid
from typing import Dict, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.modules.task.task_schemas import AsyncTaskCreateResponse, AsyncTaskCreateRequest
from app.modules.task.task_choices import AsyncTaskStatus, AsyncTaskResultType
from app.shared.storage.s3.objects import generate_s3_storage_object_key, storage_s3_save_object, storage_s3_retrieve_objects_url
from app.modules.task.task_storage_paths import TaskStoragePaths


class AsyncTaskRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection_name = "async_tasks"
        self.collection = db[self.collection_name]

    async def create(
        self, 
        background_async_tasks: BackgroundTasks, 
        func: callable, 
        params: Optional[Dict] = None,
        result_type: Optional[AsyncTaskResultType] = AsyncTaskResultType.RAW_RESULT
    ) -> AsyncTaskCreateResponse:

        if params is None:
            params = {}

        raw_async_task = AsyncTaskCreateRequest(
            result_type=result_type.value
        )
        async_task = await self.collection.insert_one(
            raw_async_task.model_dump()
        )
        async_task_id = async_task.inserted_id

        async def task_runner():
            try:
                await self.collection.update_one(
                    {"_id": async_task_id},
                    {"$set": {"status": AsyncTaskStatus.IN_PROGRESS.value, "progress": 0}}
                )

                if asyncio.iscoroutinefunction(func):
                    result = await func(**params)
                else:
                    loop = asyncio.get_running_loop()
                    result = await loop.run_in_executor(None, func, **params)

                if result_type == AsyncTaskResultType.ARCHIVE:
                    base_async_task_path = TaskStoragePaths(self.db.name).async_task(async_task_id)
                    relative_save_path = generate_s3_storage_object_key(prefix=base_async_task_path, file=result)
                    storage_s3_save_object(file=result, relative_save_path=relative_save_path)
                    result = relative_save_path

                await self.collection.update_one(
                    {"_id": async_task_id},
                    {"$set": {"status": AsyncTaskStatus.COMPLETED.value, "progress": 100, "result": result}}
                )
            except Exception as error:
                await self.collection.update_one(
                    {"_id": async_task_id},
                    {"$set": {"status": AsyncTaskStatus.FAILED.value, "error": str(error)}}
                )

        background_async_tasks.add_task(task_runner)

        return AsyncTaskCreateResponse(
            _id=str(async_task_id),
            status=AsyncTaskStatus.PENDING.value
        )