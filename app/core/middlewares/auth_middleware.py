from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, HTTPException
from starlette.status import HTTP_401_UNAUTHORIZED
from app.modules.auth.auth_service import AuthService
from app.shared.handle_decorator import handle_decorator

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method == "OPTIONS":
            return await call_next(request)

        if request.url.path.startswith(("/docs", "/redoc", "/openapi.json")):
            return await call_next(request)
        
        if handle_decorator("no_auth", request):
            return await call_next(request)

        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=HTTP_401_UNAUTHORIZED,
                detail="Token not provided."
            )

        if request.app.state.testing:
            return await call_next(request)

        token = auth_header.split("Bearer ")[1].strip()
        if not await AuthService().validate_token(token):
            raise HTTPException(
                status_code=HTTP_401_UNAUTHORIZED,
                detail="Invalid token."
            )

        return await call_next(request)