from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime
import os

load_dotenv()

app = FastAPI()
client = AsyncIOMotorClient(os.getenv("MONGO_URI"))
db_global = client[os.getenv("MONGO_DB_GLOBAL")]
clients_col = db_global["clients"]

class ClientSchema(BaseModel):
    name: str

@app.post("/client")
async def create(client: ClientSchema):
    if clients_col.find_one({"name": client.name}):
        raise HTTPException(status_code=400, detail="Cliente já existe")
    
    client_data = {
        "name": client.name,
        "active": True,
        "created_at": datetime.now()
    }
    clients_col.insert_one(client_data)

    db_client = client[f"client_{client.name}"]
    db_client.users.insert_one({
        "name": "Admin",
        "email": f"admin@{client.name}.com",
        "password": f"admin@{client.name}"
    })
    db_client.users.create_index("email", unique=True)

    return {"status": "success", "client": client.name}

@app.get("/client")
async def read():
    clients = list(clients_col.find({}, {"_id": 0}))
    return clients

@app.put("/client/{client_id}")
async def update_client(client_id: str, new: ClientSchema):
    try:
        obj_id = ObjectId(client_id)
    except Exception:
        raise HTTPException(status_code=400, detail="ID inválido")

    client = clients_col.find_one({"_id": obj_id})
    if not client:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    
    clients_col.update_one({"_id": obj_id}, {"$set": {"name": new.name}})
    
    return {
        "status": "success",
        "old": client["name"],
        "new": new.name
    }

@app.delete("/client/{client_id}")
async def inactivate(client_id: str):
    try:
        obj_id = ObjectId(client_id)
    except Exception:
        raise HTTPException(status_code=400, detail="ID inválido")

    client = clients_col.find_one({"_id": obj_id})
    if not client:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    
    clients_col.update_one({"name": client["name"]}, {"$set": {"ativo": False}})
    return {"status": "sucesso", "client": client["name"], "ativo": False}
