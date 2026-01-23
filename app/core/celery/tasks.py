from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.celery.celery_app import celery_app
from app.modules.task.task_choices import AsyncTaskType, AsyncTaskStatus
from app.modules.task.task_factory import AsyncTaskFactory
from app.shared.database.connection import get_connection
from app.shared.database.object_management import update_attributes
import asyncio

ASYNC_TASKS_COLLECTION = "async_tasks"

@celery_app.task(bind=True)
def celery_task(self, *, task_id: str, task_type: str, db_name: str, params: dict):
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    db = get_connection(db_name)
    try:
        spec = AsyncTaskFactory.get_spec(AsyncTaskType(task_type))
        handler = spec.handler
        runner = handler(
            task_id=task_id,
            db=db,
            result_type=spec.result_type
        )
        loop.run_until_complete(runner.run(params))
    except Exception as error:
        loop.run_until_complete(
            update_attributes(
                collection=db[ASYNC_TASKS_COLLECTION],
                object_id=task_id,
                status=AsyncTaskStatus.FAILED.value,
                log=str(error)
            )
        )
        raise
