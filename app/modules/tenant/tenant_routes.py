import datetime
from bson import ObjectId
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict
from app.core.database import MongoConnection
from app.core.decorators.auth_decorator import no_auth
from app.core.decorators.tenant_decorator import no_tenant_required

class TenantSchema(BaseModel):
    _id: ObjectId
    name: str
    database: str
    admin_email: str
    is_active: bool

    model_config = ConfigDict(extra="allow")

router = APIRouter(prefix="/tenant", tags=["Tenant"])
client = MongoConnection.get_client()

@no_auth
@no_tenant_required
@router.post("/")
async def create(tenant: TenantSchema):
    existing_dbs = await client.list_database_names()
    
    if tenant.database in existing_dbs:
        raise HTTPException(
            status_code=400,
            detail=f"Tenant '{tenant.name}' já existe (database {tenant.database} encontrado)"
        )
    
    tenant_db = client[tenant.database]
    tenant.created_at = f"{datetime.datetime.utcnow()}"
    result = await tenant_db.dummy.insert_one(dict(tenant))
    
    tenant_dict = dict(tenant)
    tenant_dict['_id'] = str(result.inserted_id)

    return dict(tenant)

@no_auth
@no_tenant_required
@router.get("/")
async def read():
    all_dbs = await client.list_database_names()
    
    tenant_dbs = [db for db in all_dbs if db.startswith("cp_")]
    
    tenants_info = []
    
    for db_name in tenant_dbs:
        tenant_name = db_name.replace("cp_", "", 1)
        tenant_db = client[db_name]
        
        info_doc = await tenant_db.dummy.find_one({})
        
        if info_doc:
            tenant_data = {
                "_id": str(info_doc.get("_id")) ,
                "name": info_doc.get("name"),
                "database": info_doc.get("database"),
                "admin_email": info_doc.get("admin_email"),
                "active": info_doc.get("active", True),
                "created_at": info_doc.get("created_at"),
            }
        else:
            tenant_data = {
                "name": tenant_name,
                "database": db_name,
                "note": "Informações detalhadas não encontradas"
            }
        
        tenants_info.append(tenant_data)
    
    tenants_info.sort(key=lambda x: x.get("company_name", "").lower())
    
    return {
        "total": len(tenants_info),
        "tenants": tenants_info
    }

@router.put("/{tenant_id}")
async def update_tenant(tenant_id: str, new: TenantSchema):
    try:
        obj_id = ObjectId(tenant_id)
    except Exception:
        raise HTTPException(status_code=400, detail="ID inválido")

    tenant = tenants_collection.find_one({"_id": obj_id})
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant não encontrado")
    
    tenants_collection.update_one({"_id": obj_id}, {"$set": {"name": new.name}})
    
    return {
        "status": "success",
        "old": tenant["name"],
        "new": new.name
    }

@router.delete("/{tenant_id}")
async def inactivate(tenant_id: str):
    try:
        obj_id = ObjectId(tenant_id)
    except Exception:
        raise HTTPException(status_code=400, detail="ID inválido")

    tenant = tenants_collection.find_one({"_id": obj_id})
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant não encontrado")
    
    tenants_collection.update_one({"name": tenant["name"]}, {"$set": {"ativo": False}})
    return {"status": "sucesso", "tenant": tenant["name"], "ativo": False}
