from fastapi import FastAPI
from app.modules.item.item_routes import router as item_router

app = FastAPI(title="FastAPI + MongoDB")

app.include_router(item_router)
