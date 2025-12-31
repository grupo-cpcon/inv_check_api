from pydantic import BaseModel
from typing import Optional

class ErrorResponse(BaseModel):
    status_code: int
    detail: str
    error_code: Optional[str] = None