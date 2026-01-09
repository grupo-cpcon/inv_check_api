from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import HTTPException, Request
from app.core.database import MongoConnection
from app.shared.handle_decorator import handle_decorator
from app.shared.mongo_indexes import create_indexes
from app.main import INITIALIZED_TENANTS

class TenantMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method == "OPTIONS":
            return await call_next(request)

        if request.url.path.startswith(("/docs", "/redoc", "/openapi.json")):
            return await call_next(request)
        
        if handle_decorator("no_tenant_required", request):
            return await call_next(request)

        tenant_name = request.headers.get("tenant")
        
        if not tenant_name:
            raise HTTPException(
                status_code=400,
                detail="Header 'tenant' é obrigatório"
            )

        if not tenant_name.replace("_", "").replace("-", "").isalnum():
            raise HTTPException(
                status_code=400,
                detail="Nome do tenant inválido"
            )

        db_name = tenant_name

        client = MongoConnection.get_client()

        existing_dbs = await client.list_database_names()

        if db_name not in existing_dbs:
            raise HTTPException(
                status_code=404,
                detail=f"Tenant '{tenant_name}' não encontrado"
            )
  
        db = client.get_database(db_name)

        if tenant_name not in INITIALIZED_TENANTS:
            await create_indexes(db)
            INITIALIZED_TENANTS.add(tenant_name)

        request.state.db = db

        return await call_next(request)