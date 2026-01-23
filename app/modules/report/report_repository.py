from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime

from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

from app.shared.storage.s3.objects import storage_s3_retrieve_objects_url
from app.modules.report.report_schemas import ItemNodeDTO

from io import BytesIO
from starlette.datastructures import UploadFile
from zoneinfo import ZoneInfo

from app.shared.datetime import time_now
import json

class ReportAnaliticalService:
    def __init__(self, database: AsyncIOMotorDatabase):
        self.db = database

    # only for debug, shit
    def to_json_safe(self, obj):
        if isinstance(obj, dict):
            return {
                str(k): self.to_json_safe(v)
                for k, v in obj.items()
            }
        elif isinstance(obj, list):
            return [self.to_json_safe(i) for i in obj]
        elif isinstance(obj, ObjectId):
            return str(obj)
        elif isinstance(obj, datetime):
            return obj.isoformat()
        else:
            return obj

    async def create_analitical_report(self, parent_location_ids: Optional[List[str]]) -> UploadFile:
        data = await self.build_data(parent_location_ids)
        json_safe_data = self.to_json_safe(data)
        print(json.dumps(json_safe_data, indent=4, ensure_ascii=False))

        env = Environment(
            loader=FileSystemLoader("app/template"),
            autoescape=True
        )

        template = env.get_template("report/analytical/report.html")

        html_content = template.render(
            tree=tree,
            generated_at=time_now().strftime(
                "%d/%m/%Y %H:%M"
            )
        )

        pdf_bytes = BytesIO()
        HTML(string=html_content).write_pdf(target=pdf_bytes)
        pdf_bytes.seek(0)

        upload_file = UploadFile(
            filename="relatorio_analitico.pdf",
            file=BytesIO(pdf_bytes.read())
        )

        return upload_file

    async def build_data(self, parent_locations_ids: Optional[List[str]] = None) -> Dict[Tuple[str, str], List[Dict]]:
        locations_ids = await self.get_all_descendant_locations(parent_locations_ids)
        loc_obj_ids = [ObjectId(l_id) for l_id in locations_ids]

        loc_docs = await self.db.inventory_items.find({"_id": {"$in": loc_obj_ids}}, {"_id": 1, "path": 1}).to_list(None)
        loc_map = {l["_id"]: (str(l["_id"]), " -> ".join(l.get("path", []))) for l in loc_docs}

        pipeline = [
            {"$match": {"parent_id": {"$in": loc_obj_ids}, "node_type": {"$ne": "LOCATION"}}},
            {
                "$graphLookup": {
                    "from": "inventory_items",
                    "startWith": "$_id",
                    "connectFromField": "_id",
                    "connectToField": "parent_id",
                    "as": "descendants",
                    "restrictSearchWithMatch": {"node_type": {"$ne": "LOCATION"}}
                }
            },
            {"$addFields": {"root_loc": "$parent_id"}},
            {"$project": {"docs": {"$concatArrays": [["$$ROOT"], "$descendants"]}, "root_loc": 1}},
            {"$unwind": "$docs"},
            {"$addFields": {"docs.root_loc": "$root_loc"}},
            {"$replaceRoot": {"newRoot": "$docs"}},
            {"$project": {"descendants": 0}}
        ]
        
        flattened_items = await self.db.inventory_items.aggregate(pipeline).to_list(None)

        result: Dict[Tuple[str, str], List[Dict]] = {}
        for item in flattened_items:
            root_loc_id = item.get("root_loc")
            key = loc_map.get(root_loc_id)
            if key:
                if key not in result:
                    result[key] = []
                result[key].append(item)

        return result
        
    async def get_all_descendant_locations(
        self, parent_location_ids: Optional[List[str]] = None
    ) -> List[str]:
        if not parent_location_ids:
            docs = await self.db.inventory_items.find(
                {"node_type": "LOCATION"}, {"_id": 1}
            ).to_list(None)
            return [str(doc["_id"]) for doc in docs]

        obj_ids = [ObjectId(pid) for pid in parent_location_ids]

        pipeline = [
            {"$match": {"_id": {"$in": obj_ids}}},
            {
                "$graphLookup": {
                    "from": "inventory_items",
                    "startWith": "$_id",
                    "connectFromField": "_id",
                    "connectToField": "parent_id",
                    "as": "descendants"
                }
            },
            {"$unwind": "$descendants"},
            {"$match": {"descendants.node_type": "LOCATION"}},
            {"$group": {"_id": "$descendants._id"}}
        ]

        cursor = self.db.inventory_items.aggregate(pipeline)
        results = await cursor.to_list(None)
        
        return [str(doc["_id"]) for doc in results]
