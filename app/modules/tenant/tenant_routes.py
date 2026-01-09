import datetime
from typing import List

from bson import ObjectId
from fastapi import APIRouter, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorCollection
from pymongo import ReturnDocument

from app.core.database import MongoConnection
from app.core.decorators.tenant_decorator import no_tenant_required
from fastapi import Request

from app.modules.tenant.tenant_schema import TenantCreateUpdateDTO, TenantSchema, TenantResponseDTO, \
    TenantListResponseDTO
from app.modules.tenant.tenant_service import get_tenant_database_names


router = APIRouter(prefix="/tenant", tags=["Tenant"])
client = MongoConnection.get_client()


@no_tenant_required
@router.post(
    path="/",
    response_model=TenantResponseDTO,
    status_code=status.HTTP_201_CREATED
)
async def create_tenant(payload: TenantCreateUpdateDTO):
    existing_dbs: List[str] = await client.list_database_names()
    
    if payload.database in existing_dbs:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Tenant '{payload.name}' já existe (database '{payload.database}' encontrada)"
        )

    tenant_db_model: TenantSchema = TenantSchema(
        _id=ObjectId(),
        database=payload.database,
        name=payload.name,
        is_active=True,
        created_at=datetime.datetime.now(datetime.UTC)
    )

    # Reference to the database
    tenant_db: AsyncIOMotorDatabase = client[payload.database]

    # Insert document into dummy collection so Mongo actually creates the tenant
    await tenant_db.dummy.insert_one(
        tenant_db_model.model_dump(by_alias=True) # by_alias has to be true so we insert '_id' instead of 'id'
    )

    return tenant_db_model


@no_tenant_required
@router.get(
    path="/",
    response_model=TenantListResponseDTO,
    status_code=status.HTTP_200_OK
)
async def list_tenants():
    tenant_dbs: List[str] = await get_tenant_database_names()
    tenants_info: List[dict] = []
    
    for db_name in tenant_dbs:
        tenant_name: str = db_name.replace("cp_", "", 1)
        tenant_db: AsyncIOMotorDatabase = client[db_name]
        
        info_doc: dict = await tenant_db.dummy.find_one()
        
        if info_doc:
            tenant_data = TenantResponseDTO.model_validate(info_doc)
        else:
            tenant_data = {
                "name": tenant_name,
                "database": db_name,
                "note": "Informações detalhadas não encontradas"
            }
        
        tenants_info.append(tenant_data)

    tenants_info.sort(key=lambda x: getattr(x, "name", "").lower())

    return {
        "total": len(tenants_info),
        "tenants": tenants_info
    }


@router.put(
    path="/",
    response_model=TenantResponseDTO,
    status_code=status.HTTP_200_OK
)
async def update_tenant(payload: TenantCreateUpdateDTO, request: Request):
    db: AsyncIOMotorDatabase = request.state.db
    dummy_collection: AsyncIOMotorCollection = db.dummy

    updated: dict = await dummy_collection.find_one_and_update(
        filter={},  # There is only 1 dummy
        update={"$set": payload.model_dump(exclude_unset=True)},
        return_document=ReturnDocument.AFTER,
    )

    if not updated:
        raise HTTPException(
            status_code=404,
            detail="Tenant não encontrado"
        )

    return updated


@router.delete(
    path="/",
    response_model=TenantResponseDTO,
    status_code=status.HTTP_200_OK
)
async def inactivate_tenant(request: Request):
    db: AsyncIOMotorDatabase = request.state.db
    dummy_collection: AsyncIOMotorCollection = db.dummy

    updated: dict = await dummy_collection.find_one_and_update(
        filter={},  # There is only 1 dummy
        update={"$set": {"is_active": False}},
        return_document=ReturnDocument.AFTER,
    )

    if not updated:
        raise HTTPException(
            status_code=404,
            detail="Tenant não encontrado"
        )

    return updated
