from typing import List
import pandas as pd
from fastapi import File, UploadFile
from app.services.excel_services import build_tree_from_df, clean


class DataLoadRepository:
    async def create_many(self, file: UploadFile = File(...), extra_fields: List[str] = []):
        df = pd.read_excel(file.file)

        tree = build_tree_from_df(df, delimiter_column="delimiter", extra_fields=extra_fields)
        
        for r in tree:
            clean(r)

        try:
            result = await collection.insert_many(tree)
            return {"message": "Dados inseridos com sucesso!", "count": len(tree)}
        except:
            return {"message": "Não foi possível fazer a carga de itens"}

        