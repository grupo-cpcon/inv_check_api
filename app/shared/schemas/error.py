from pydantic import BaseModel
from typing import Optional, Union

class ErrorResponse(BaseModel):
    status_code: int
    detail: Union[str, list]
    error_code: Optional[str] = None