from bson import ObjectId
from fastapi import APIRouter, Query, Request
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.modules.task.task_choices import AsyncTaskResultType
from app.modules.task.task_schemas import AsyncTaskCreateResponse
from app.modules.task.task_repository import AsyncTaskRepository
from fastapi import BackgroundTasks, status

# schemas
from app.modules.report.report_schemas import (
    CreateAnalyticalReportRequest
)

# services
from app.modules.report.report_repository import (
    ReportAnaliticalService
)

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
    
    cursor = db.inventory_items.find(
        query, {}
    ).sort("reference", 1).skip(skip).limit(limit)
    
    items = []
    total_count = await db.inventory_items.count_documents(query)
    
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
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

@router.get("/dashboard")
async def dashboard_session(request: Request):
    db: AsyncIOMotorDatabase = request.state.db
    
    total = await db.inventory_items.count_documents({
        "node_type": "ASSET"
    })

    inventoried = await db.inventory_items.count_documents({
        "checked": True
    })

    percent = round((inventoried / total) * 100, 2) if total else 0

    return {
        "total_items": total,
        "inventoried": inventoried,
        "pending": total - inventoried,
        "percent": percent
    }

@router.post(
    "/analytical", 
    response_model=AsyncTaskCreateResponse,
    status_code=status.HTTP_202_ACCEPTED
)
async def create_analytical_report(
    request: Request, 
    background_tasks: BackgroundTasks,
    payload: CreateAnalyticalReportRequest    
) -> AsyncTaskCreateResponse:   

    parent_ids = payload.parent_ids
    task_repository = AsyncTaskRepository(request.state.db)

    async_task = await task_repository.create(
        background_async_tasks=background_tasks,
        func=ReportAnaliticalService(request.state.db).create_analitical_report,
        params={"parent_ids": parent_ids},
        result_type=AsyncTaskResultType.ARCHIVE
    )

    return async_task