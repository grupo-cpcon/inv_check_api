from motor.motor_asyncio import AsyncIOMotorCollection
from bson import ObjectId
from typing import Dict, Any


async def update_attributes(collection: AsyncIOMotorCollection, object_id: ObjectId, **extra: Dict[Any, Any]) -> None:
    await collection.update_one(
        {"_id": object_id},
        {"$set": {**extra}},
    )