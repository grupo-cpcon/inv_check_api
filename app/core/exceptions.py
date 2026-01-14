from fastapi.responses import JSONResponse
from fastapi import Request
from app.shared.schemas.error import ErrorResponse
from fastapi.exceptions import RequestValidationError
from fastapi import HTTPException
from app.shared.exceptions.base import AppError


def raise_error(status_code: int, detail: str, error_code: str = None):
    error = ErrorResponse(
        status_code=status_code,
        detail=detail,
        error_code=error_code
    )
    return JSONResponse(status_code=status_code, content=error.dict())

async def http_exception_handler(request: Request, exc: Exception):

    if isinstance(exc, RequestValidationError):
        return JSONResponse(
            status_code=422,
            content=ErrorResponse(
                status_code=422,
                detail=exc.errors(),
                error_code="VALIDATION_ERROR"
            ).dict()
        )

    if isinstance(exc, AppError):
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                status_code=exc.status_code,
                detail=exc.message,
                error_code=exc.error_code
            ).dict()
        )

    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                status_code=exc.status_code,
                detail=exc.detail,
                error_code="HTTP_ERROR"
            ).dict()
        )

    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            status_code=500,
            detail="Internal server error",
            error_code="INTERNAL_ERROR"
        ).dict()
    )