from http import client
from fastapi import Request

@app.middleware("http")
async def tenant_middleware(request: Request, call_next):
    client_name = request.headers.get("client_name")
    request.state.db_client = client[f"client_{client_name}"]
    response = await call_next(request)
    return response