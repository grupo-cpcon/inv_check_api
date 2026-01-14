from bson import ObjectId
from fastapi import APIRouter, Query, Request
from app.core.decorators.auth_decorator import no_auth

router = APIRouter(prefix="/report", tags=["Report"])

@router.get("/tree/children")
async def get_items(
    request: Request,
    parent_id: str | None = Query(default=None, description="ID do item pai. Vazio para itens raiz."),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100)
):
    db = request.state.db

    query = {"parent_id": None}
    
    if parent_id:
        query = {"parent_id": ObjectId(parent_id)}
    
    cursor = db.inventory_checks.find(
        query, {}
    ).sort("reference", 1).skip(skip).limit(limit)
    
    items = []
    total_count = await db.inventory_checks.count_documents(query)
    
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        doc["session_id"] = str(doc["session_id"])
        doc["item_id"] = str(doc["item_id"])
        if doc.get("parent_id"):
            doc["parent_id"] = str(doc["parent_id"])
            
        items.append(doc)
    
    return {
        "items": items,
        "total": total_count,
        "skip": skip,
        "limit": limit,
        "has_more": (skip + limit) < total_count
    }