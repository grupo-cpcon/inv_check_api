from fastapi import FastAPI, HTTPException
from app.core.middlewares.tenant_middleware import TenantMiddleware
from fastapi.exceptions import RequestValidationError
from app.core.exceptions import http_exception_handler  
from app.core.events.server_events import startup_events

app = FastAPI(title="FastAPI + MongoDB")
app.state.public_endpoints = set()
app.state.no_tenant_required_endpoints = set()

# events
# shutdown_events(app)
startup_events(app)

# exception
app.add_exception_handler(Exception, http_exception_handler)
app.add_exception_handler(RequestValidationError, http_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)

# middleware
from app.core.middlewares.auth_middleware import AuthMiddleware
app.add_middleware(AuthMiddleware)
app.add_middleware(TenantMiddleware)

# routes
from app.modules.item.item_routes import router as item_router
from app.modules.auth.auth_routes import router as auth_router
from app.modules.data_load.data_load_routes import router as data_load_router
from app.modules.tenant.tenant_routes import router as tenant_router

app.include_router(tenant_router)
app.include_router(data_load_router)
app.include_router(item_router)
app.include_router(auth_router)