from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from app.core.exceptions import http_exception_handler  
from app.core.database import connect_to_mongo, close_mongo_connection
from app.core.events.server_events import shutdown_events, startup_events

app = FastAPI(title="FastAPI + MongoDB")
app.state.public_endpoints = set()

# events
shutdown_events(app)
startup_events(app)

# exception
app.add_exception_handler(Exception, http_exception_handler)
app.add_exception_handler(RequestValidationError, http_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)

# middleware
from app.core.middlewares.auth_middleware import AuthMiddleware
app.add_middleware(AuthMiddleware)

# routes
from app.modules.item.item_routes import router as item_router
from app.modules.auth.auth_routes import router as auth_router

app.include_router(item_router)
app.include_router(auth_router)