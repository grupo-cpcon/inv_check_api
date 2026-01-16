from bson import ObjectId
from fastapi import Query, Request, UploadFile
import pandas as pd
from app.services.excel_services import build_nodes_from_df
from app.shared.storage.s3.objects import storage_s3_retrieve_objects_url


class DataLoadRepository:
    async def create_many(self, request: Request):
        form = await request.form()
        file: UploadFile = form.get("file")
        extra_fields: str = form.get("extra_fields", "")
    
        extra_fields_list = [
            f.strip() for f in extra_fields.split(",") if f.strip()
        ]
    
        df = pd.read_excel(file.file)
    
        documents = build_nodes_from_df(
            df,
            delimiter_column="delimiter",
            extra_fields=extra_fields_list
        )
    
        if not documents:
            return {"message": "Nenhum item para inserir"}
    
        try:
            await request.state.db.inventory_items.insert_many(documents)
            return {
                "message": "Itens inseridos com sucesso!",
                "count": len(documents)
            }
        except Exception as e:
            return {
                "message": "Erro ao inserir itens",
                "error": str(e)
            }
    
    async def get_items(    
        self,
        request: Request,
        parent_id: str | None = Query(default=None)
    ):
        db = request.state.db
    
        query = {"parent_id": None}
        if parent_id:
            query = {"parent_id": ObjectId(parent_id)}
    
        cursor = db.inventory_items.find(
            query, {}
        ).sort("reference", 1)
    
        items = []
        
        async for doc in cursor:
            if 'photos' in doc:
                doc['photos'] = await storage_s3_retrieve_objects_url(doc.get('photos', None))
            doc["_id"] = str(doc["_id"])
            if doc.get("parent_id"):
                doc["parent_id"] = str(doc["parent_id"])
            items.append(doc)
    
        return items