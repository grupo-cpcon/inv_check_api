from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from typing import Dict, List, Optional, Set
from datetime import datetime

from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

from app.shared.storage.s3.objects import storage_s3_retrieve_objects_url
from app.modules.report.report_schemas import ItemNodeDTO

from io import BytesIO
from starlette.datastructures import UploadFile
from zoneinfo import ZoneInfo

from app.shared.datetime import time_now

class ReportAnaliticalService:
    def __init__(self, database: AsyncIOMotorDatabase):
        self.db = database

    async def create_analitical_report(self, parent_ids: Optional[List[str]]) -> UploadFile:
        tree = await self.build_items_tree(parent_ids)

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

    async def build_items_tree(self, parent_ids: Optional[List[str]] = None) -> List[ItemNodeDTO]:
        valid_root_ids = await self._get_valid_roots(parent_ids)
        root_object_ids = [ObjectId(rid) for rid in valid_root_ids]

        roots_docs = await self.db.inventory_items.find(
            {"_id": {"$in": root_object_ids}},
            {
                "_id": 1,
                "reference": 1,
                "node_type": 1,
                "parent_id": 1,
                "checked": 1,
                "checked_at": 1,
                "photos": 1,
            }
        ).to_list(None)

        nodes: Dict[str, ItemNodeDTO] = {}
        roots: List[ItemNodeDTO] = []

        for doc in roots_docs:
            node_id = str(doc["_id"])
            node = ItemNodeDTO(
                _id=node_id,
                name=doc.get("reference"),
                node_type=doc.get("node_type"),
                is_checked=doc.get("checked", False),
                checked_at=doc.get("checked_at"),
                photos=await storage_s3_retrieve_objects_url(
                    doc.get("photos", [])
                ),
            )

            nodes[node_id] = node
            roots.append(node)

        queue: List[str] = list(nodes.keys())

        while queue:
            parent_id = queue.pop(0)
            parent_node = nodes[parent_id]

            children_docs = await self.db.inventory_items.find(
                {"parent_id": ObjectId(parent_id)},
                {
                    "_id": 1,
                    "reference": 1,
                    "node_type": 1,
                    "parent_id": 1,
                    "checked": 1,
                    "checked_at": 1,
                    "photos": 1,
                }
            ).to_list(None)

            for child in children_docs:
                child_id = str(child["_id"])

                if child_id in nodes:
                    continue

                child_node = ItemNodeDTO(
                    _id=child_id,
                    name=child.get("reference"),
                    node_type=child.get("node_type"),
                    is_checked=child.get("checked", False),
                    checked_at=child.get("checked_at"),
                    photos=await storage_s3_retrieve_objects_url(
                        child.get("photos", [])
                    ),
                )

                parent_node.children.append(child_node)
                nodes[child_id] = child_node
                queue.append(child_id)

        return roots

    async def _get_valid_roots(self, raw_root_ids: Optional[List[str]]) -> List[str]:
        if not raw_root_ids:
            docs = await self.db.inventory_items.find(
                {"level": 0},
                {"_id": 1}
            ).to_list(None)

            return [str(doc["_id"]) for doc in docs]

        root_object_ids = [ObjectId(rid) for rid in raw_root_ids]
        docs = await self.db.inventory_items.find(
            {"_id": {"$in": root_object_ids}},
            {"_id": 1, "parent_id": 1}
        ).to_list(None)

        id_to_parent = {
            str(doc["_id"]): str(doc["parent_id"])
            if doc.get("parent_id") else None
            for doc in docs
        }

        input_id_set: Set[str] = set(id_to_parent.keys())
        valid_roots: List[str] = []

        for item_id in input_id_set:
            current_parent = id_to_parent.get(item_id)
            is_child = False

            while current_parent:
                if current_parent in input_id_set:
                    is_child = True
                    break

                parent_doc = await self.db.inventory_items.find_one(
                    {"_id": ObjectId(current_parent)},
                    {"parent_id": 1}
                )

                if not parent_doc or not parent_doc.get("parent_id"):
                    break

                current_parent = str(parent_doc["parent_id"])

            if not is_child:
                valid_roots.append(item_id)

        return valid_roots