from typing import List

from bson import ObjectId
from fastapi import HTTPException, status

from app.core.database import MongoConnection


client = MongoConnection.get_client()


async def get_tenant_database_names() -> List[str]:
    all_dbs: List[str] = await client.list_database_names()
    tenant_dbs: List[str] = [db for db in all_dbs if db.startswith("cp_")]
    return tenant_dbs


def get_obj_id_by_tenant_id(tenant_id: str) -> ObjectId:
    try:
        obj_id: ObjectId = ObjectId(tenant_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ID do Tenant inválido"
        )
    return obj_id