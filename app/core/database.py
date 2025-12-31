import os
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB_NAME = os.getenv("MONGO_DB")

if not MONGO_URI or not MONGO_DB_NAME:
    raise ValueError("MONGO_URI or MONGO_DB_NAME not set in environment variables")

# client: Optional[AsyncIOMotorClient] = None
client = AsyncIOMotorClient(MONGO_URI)

async def connect_to_mongo():
    global client
    if client is None:
        client = AsyncIOMotorClient(MONGO_URI)

async def close_mongo_connection():
    if client:
        client.close()

def get_database():
    if client is None:
        raise RuntimeError("Mongo client is not initialized. Call connect_to_mongo() first.")
    return client[MONGO_DB_NAME]
