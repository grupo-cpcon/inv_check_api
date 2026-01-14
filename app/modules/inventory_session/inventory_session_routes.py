import io
from bson import ObjectId
from fastapi import APIRouter, Request
from datetime import datetime
from fastapi.responses import StreamingResponse
from openpyxl import Workbook
from requests import session
from app.core.decorators.auth_decorator import no_auth

router = APIRouter(prefix="/inventory-sessions", tags=["Inventory Sessions"])

@router.get("/inventory/export/{session_id}")
async def export_inventory(session_id: str, request: Request):
    db = request.state.db
    session_id = ObjectId(session_id)

    cursor = db.inventory_checks.find({"session_id": session_id})

    wb = Workbook()
    ws = wb.active
    ws.title = "Inventário"

    ws.append([
        "Item Code",
        "Localização",
        "Nível",
        "Inventariado",
        "Data",
        "Qtd Fotos"
    ])

    async for doc in cursor:
        ws.append([
            doc["reference"],
            " > ".join(doc["path"]),
            doc["level"],
            "SIM" if doc["checked"] else "NÃO",
            doc["checked_at"].strftime("%Y-%m-%d %H:%M"),
            len(doc.get("photos", []))
        ])

    stream = io.BytesIO()
    wb.save(stream)
    stream.seek(0)

    return StreamingResponse(
        stream,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename=inventory_{session_id}.xlsx"
        }
    )

@router.get("/dashboard/session/{session_id}")
async def dashboard_session(session_id: str, request: Request):
    db = request.state.db
    session_id = ObjectId(session_id)

    total = await db.inventory_items.count_documents({
        "node_type": "ASSET"
    })

    inventoried = await db.inventory_checks.count_documents({
        "session_id": session_id
    })

    percent = round((inventoried / total) * 100, 2) if total else 0

    return {
        "total_items": total,
        "inventoried": inventoried,
        "pending": total - inventoried,
        "percent": percent
    }

@router.post("")
async def create_session(body: dict, request: Request):
    db = request.state.db

    session = {
        "name": body.get("name"),
        "created_at": datetime.utcnow(),
        "status": "in_progress"
    }

    result = await db.inventory_sessions.insert_one(session)

    session["_id"] = str(result.inserted_id)

    return session

@router.get("")
async def get_sessions(request: Request):
    db = request.state.db
    cursor = db.inventory_sessions.find({}).sort("created_at", -1)
    result = await cursor.to_list()
    for doc in result:
        doc["_id"] = str(doc["_id"])

    return result