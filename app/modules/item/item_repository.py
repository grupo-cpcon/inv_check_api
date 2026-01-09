import datetime
from bson import ObjectId
from fastapi import HTTPException, Request

class ItemRepository:
    async def check_status(
        request: Request,
        session_id: str,
        item_id: str
    ):
        db = request.state.db

        exists = await db.inventory_checks.find_one({
            "session_id": ObjectId(session_id),
            "item_id": ObjectId(item_id)
        })

        return {
            "checked": bool(exists)
        }

    async def check_item(self, request: Request, body: dict):
        db = request.state.db
        form = await request.form()

        session_id = form.get("session_id")
        item_id = form.get("item_id")
        parent_id = form.get("parent_id")

        if not session_id or not item_id:
            raise HTTPException(400, "session_id, item_id e parent_id são obrigatórios")

        item = await db.inventory_nodes.find_one({"_id": item_id})
        
        if not item:
            raise HTTPException(404, "Item não encontrado")

        exists = await db.inventory_checks.find_one({
            "session_id": ObjectId(session_id),
            "item_id": ObjectId(item_id)
        })

        if exists:
            raise HTTPException(400, "Item já inventariado")

        photos_data = []
        photo_fields = []

        for key in form.keys():
            if key.startswith('photo') or key == 'photos':
                photo_fields.append(key)

        for field in photo_fields:
            photos = form.getlist(field) 

            for photo in photos:
                if hasattr(photo, 'file'):  # É um UploadFile
                    # TODO: FAZER UPLOAD PARA BUCKET AQUI
                    pass
            
        doc = {
            "session_id": ObjectId(session_id),
            "item_id": ObjectId(item_id),
            "parent_id": ObjectId(parent_id),
            "checked": True,
            "checked_at": datetime.datetime.utcnow(),
            "photos": photos_data,
            "reference": item["reference"],
            "asset_data": item["asset_data"],
            "path": item["path"]
        }

        await db.inventory_checks.insert_one(doc)

        return doc
    
    # async def find_by(self, request: Request):
    #    db = request.state.db
    #    args: dict = request.query_params
    #    cursor = db.items.find(args)
    #    results = await cursor.to_list()
        
    #    for item in results:
    #        item["_id"] = str(item["_id"])
    #    return results
