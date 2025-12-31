from fastapi import FastAPI

from app.modules.data_load.data_load_routes import router as data_load_router
from app.modules.item.item_routes import router as item_router
from app.core.multi_tenancy_database import router as multi_tenancy_router

app = FastAPI(title="FastAPI + MongoDB")

app.include_router(multi_tenancy_router)
app.include_router(data_load_router)
app.include_router(item_router)
