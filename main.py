from fastapi import FastAPI

from app.modules.base_data.data_load_routes import data_load

app = FastAPI(title="FastAPI + MongoDB")

app.include_router(data_load)
