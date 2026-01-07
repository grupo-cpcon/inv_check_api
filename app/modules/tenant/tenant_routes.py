import datetime
from typing import List

from bson import ObjectId
from fastapi import APIRouter, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorCollection
from pydantic import BaseModel
from pymongo import ReturnDocument
from pymongo.results import InsertOneResult
from starlette.responses import Response

from app.core.database import MongoConnection
from app.core.decorators.tenant_decorator import no_tenant_required
from fastapi import Request

from app.modules.tenant.tenant_service import get_tenant_database_names, get_obj_id_by_tenant_id


class TenantSchema(BaseModel):
    _id:        ObjectId
    database:   str
    name:       str
    is_active:  bool = True
    created_at: datetime.datetime

router = APIRouter(prefix="/tenant", tags=["Tenant"])
client = MongoConnection.get_client()


@no_tenant_required
@router.post(path="/", status_code=status.HTTP_201_CREATED)
async def create(tenant: TenantSchema):
    existing_dbs: List[str] = await client.list_database_names()
    
    if tenant.database in existing_dbs:
        HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant '{tenant.name}' já existe (database {tenant.database} encontrado)"
        )

    tenant.created_at = datetime.datetime.now(datetime.UTC)

    # Reference to the database
    tenant_db: AsyncIOMotorDatabase = client[tenant.database]

    # Create dummy collection inside the database so mongo actually creates it
    result: InsertOneResult = await tenant_db.dummy.insert_one(dict(tenant))

    tenant_dict: dict = tenant.model_dump()
    tenant_dict['_id'] = str(result.inserted_id)

    return tenant_dict


@no_tenant_required
@router.get(path="/", status_code=status.HTTP_200_OK)
async def read():
    tenant_dbs: List[str] = await get_tenant_database_names()
    tenants_info: List[dict] = []
    
    for db_name in tenant_dbs:
        tenant_name: str = db_name.replace("cp_", "", 1)
        tenant_db: AsyncIOMotorDatabase = client[db_name]
        
        info_doc: dict = await tenant_db.dummy.find_one()
        
        if info_doc:
            tenant_data = info_doc
        else:
            tenant_data = {
                "name": tenant_name,
                "database": db_name,
                "note": "Informações detalhadas não encontradas"
            }
        
        tenants_info.append(tenant_data)
    
    tenants_info.sort(key=lambda x: x.get("company_name", "").lower())
    
    return Response(
        content={
            "total": len(tenants_info),
            "tenants": tenants_info,
        },
        status_code=status.HTTP_200_OK
    )


@router.put(path="/{tenant_id}", status_code=status.HTTP_200_OK)
async def update_tenant(tenant_id: str, new: TenantSchema, request: Request):
    obj_id: ObjectId = get_obj_id_by_tenant_id(tenant_id)

    db: AsyncIOMotorDatabase = request.state.db
    dummy_collection: AsyncIOMotorCollection = db.dummy
    
    updated: dict = await dummy_collection.find_one_and_update(
        filter={"_id": obj_id},
        update={"$set": new.model_dump(exclude_unset=True)},
        return_document=ReturnDocument.AFTER,
    )
    
    return Response(
        content=updated,
        status_code=status.HTTP_200_OK
    )


@router.delete("/{tenant_id}")
async def inactivate(tenant_id: str, request: Request):
    obj_id: ObjectId = get_obj_id_by_tenant_id(tenant_id)

    db: AsyncIOMotorDatabase = request.state.db
    dummy_collection: AsyncIOMotorCollection = db.dummy
    
    updated: dict = await dummy_collection.find_one_and_update(
        filter={"_id": obj_id},
        update={"$set": {"active": False}},
        return_document=ReturnDocument.AFTER,
    )

    return Response(
        content=updated,
        status_code=status.HTTP_200_OK
    )
