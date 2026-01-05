from fastapi import Request, UploadFile
import pandas as pd
from app.services.excel_services import build_tree_from_df, clean

class DataLoadRepository:
    async def create_many(self, request: Request):
        form = await request.form()
        file: UploadFile = form.get("file")
        extra_fields: str = form.get("extra_fields")
        
        extra_fields_list = [f.strip() for f in extra_fields.split(',') if f.strip()]
    
        df = pd.read_excel(file.file)

        tree = build_tree_from_df(df, delimiter_column="delimiter", extra_fields=extra_fields_list)
        
        for r in tree:
            clean(r)

        try:
            result = await request.state.db.items.insert_many(tree)
            return {"message": "Dados inseridos com sucesso!", "count": len(tree)}
        except:
            return {"message": "Não foi possível fazer a carga de itens"}

        