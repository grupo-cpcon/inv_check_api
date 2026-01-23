from fastapi import APIRouter, Request
from fastapi import HTTPException
from bson import ObjectId
from app.modules.task.task_choices import AsyncTaskResultType
from app.shared.storage.s3.objects import storage_s3_retrieve_objects_url
from app.modules.task.task_schemas import AsyncTaskListResponse


router = APIRouter(prefix="/task", tags=["Task"])

@router.get("/async-task/{task_id}", response_model=AsyncTaskListResponse)
async def retreave_task(request: Request, task_id: str) -> AsyncTaskListResponse:
    try:
        task_id = ObjectId(task_id)
    except Exception:
        raise HTTPException(status_code=400, detail=f"Invalid ObjectId: {task_id}.")

    db = request.state.db
    async_task = await db.async_tasks.find_one({"_id": task_id})

    if not async_task:
        raise HTTPException(status_code=404, detail="Task not found.")

    if (
        async_task.get("status", None) == "COMPLETED" 
        and async_task.get("result_type", None) == AsyncTaskResultType.ARCHIVE.value
        and async_task.get("result", None)
    ):
        async_task["result"] = await storage_s3_retrieve_objects_url(async_task["result"])

    return AsyncTaskListResponse(
        _id=str(async_task["_id"]),
        status=async_task["status"],
        result_type=async_task["result_type"],
        progress=async_task["progress"],
        result=async_task["result"],
        error=async_task.get("error")
    )