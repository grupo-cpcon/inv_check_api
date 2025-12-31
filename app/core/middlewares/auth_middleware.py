from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, HTTPException
from starlette.status import HTTP_401_UNAUTHORIZED
from app.modules.auth.auth_service import AuthService
from fastapi.routing import APIRoute
from starlette.routing import Match

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path.startswith(("/docs", "/redoc", "/openapi.json")):
            return await call_next(request)

        for route in request.app.routes:
            if isinstance(route, APIRoute):
                match, _ = route.matches(request.scope)
                if match == Match.FULL:
                    endpoint_func = route.endpoint
                    if getattr(endpoint_func, "no_auth", False):
                        return await call_next(request)
                    break 

        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=HTTP_401_UNAUTHORIZED,
                detail="Token not provided."
            )

        token = auth_header.split("Bearer ")[1].strip()
        if not await AuthService().validate_token(token):
            raise HTTPException(
                status_code=HTTP_401_UNAUTHORIZED,
                detail="Invalid token."
            )

        return await call_next(request)