from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")

if not MONGO_URI:
    raise ValueError("MONGO_URI not set in environment variables")

class MongoConnection:
    _client: AsyncIOMotorClient | None = None

    @classmethod
    def get_client(cls) -> AsyncIOMotorClient:
        if cls._client is None:
            cls._client = AsyncIOMotorClient(
                MONGO_URI,
                maxPoolSize=50,          
                minPoolSize=10,
                maxIdleTimeMS=30000,
                serverSelectionTimeoutMS=5000,
                port=27017
            )
        return cls._client

    @classmethod
    def get_database(cls, db_name: str):
        client = cls.get_client()
        return client[db_name]
