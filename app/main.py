from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from app.core.events.server_events import startup_events
from app.core.exceptions import http_exception_handler
from dotenv import load_dotenv

load_dotenv()


app = FastAPI(title="FastAPI + MongoDB")
app.state.public_endpoints = set()
app.state.no_tenant_required_endpoints = set()
INITIALIZED_TENANTS = set()

# events
# shutdown_events(app)
startup_events(app)

# exception
app.add_exception_handler(Exception, http_exception_handler)
app.add_exception_handler(RequestValidationError, http_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)

# middleware
from fastapi.middleware.cors import CORSMiddleware
from app.core.middlewares.tenant_middleware import TenantMiddleware
from app.core.middlewares.auth_middleware import AuthMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8080",
        "http://localhost",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(AuthMiddleware)
app.add_middleware(TenantMiddleware)

# routes
from app.modules.item.item_routes import router as item_router
from app.modules.auth.auth_routes import router as auth_router
from app.modules.data_load.data_load_routes import router as data_load_router
from app.modules.tenant.tenant_routes import router as tenant_router
from app.modules.inventory_session.inventory_session_routes import router as inventory_session_router
from app.modules.report.report_routes import router as report_router

app.include_router(tenant_router)
app.include_router(data_load_router)
app.include_router(inventory_session_router)
app.include_router(item_router)
app.include_router(auth_router)
app.include_router(report_router)

def create_test_app():
    app = FastAPI()
    app.add_middleware(TenantMiddleware)
    app.add_middleware(AuthMiddleware)
    app.include_router(tenant_router)
    app.include_router(data_load_router)
    app.include_router(inventory_session_router)
    app.include_router(item_router)
    app.include_router(auth_router)
    return app