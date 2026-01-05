from fastapi.responses import JSONResponse
from fastapi import Request
from app.shared.schemas.error import ErrorResponse
from fastapi.exceptions import RequestValidationError
from fastapi import HTTPException



def raise_error(status_code: int, detail: str, error_code: str = None):
    error = ErrorResponse(
        status_code=status_code,
        detail=detail,
        error_code=error_code
    )
    return JSONResponse(status_code=status_code, content=error.dict())

async def http_exception_handler(request: Request, exc: Exception):
    if isinstance(exc, RequestValidationError):
        detail = exc.errors()
        status_code = 422
        error_code = "VALIDATION_ERROR"
    elif isinstance(exc, HTTPException):
        detail = getattr(exc, "detail", str(exc))
        status_code = exc.status_code
        error_code = getattr(exc, "error_code", None)
    else:
        detail = str(exc)
        status_code = 500
        error_code = None

    error = ErrorResponse(
        status_code=status_code,
        detail=detail,
        error_code=error_code
    )
    return JSONResponse(status_code=status_code, content=error.dict())
