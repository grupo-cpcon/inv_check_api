from pydantic import BaseModel, Field
from typing import Any, Optional
from app.modules.task.task_choices import AsyncTaskStatus, AsyncTaskResultType, AsyncTaskType
from datetime import datetime
from app.shared.datetime import time_now
from dataclasses import dataclass
from fastapi import UploadFile


class AsyncTaskCreateRequest(BaseModel):
    status: AsyncTaskStatus = AsyncTaskStatus.PENDING.value
    task_type: AsyncTaskType
    input_file: Optional[UploadFile] = None
    result_type: AsyncTaskResultType
    progress: int = 0
    result: Optional[Any] = None
    log: Optional[str] = None
    created_at: datetime = Field(
        default_factory=lambda: time_now()
    )

class AsyncTaskListResponse(BaseModel):
    id: str = Field(alias="_id")
    status: AsyncTaskStatus
    result_type: AsyncTaskResultType
    progress: int
    result: Optional[Any] = None
    log: Optional[str] = None

    model_config = {
        "from_attributes": True,
        "populate_by_name": True
    }

class AsyncTaskCreateResponse(BaseModel):
    id: str = Field(alias="_id")
    status: AsyncTaskStatus

    model_config = {
        "from_attributes": True,
        "populate_by_name": True
    }

@dataclass(frozen=True)
class AsyncTaskSpec:
    handler: callable
    result_type: AsyncTaskResultType