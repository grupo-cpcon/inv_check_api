from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from typing import List, Optional, Dict, Any
from io import BytesIO
import asyncio
from dataclasses import fields

from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
from starlette.datastructures import UploadFile

from app.shared.storage.s3.objects import storage_s3_retrieve_objects_url
from app.shared.storage.utils import download_file_base64
from app.shared.datetime import time_now
import pandas
from openpyxl.styles import PatternFill, Font
from openpyxl.utils import get_column_letter
from pathlib import Path

from colorsys import hls_to_rgb

from app.modules.report.report_schemas import (
    InventoryResposabilityAgreementItemDTO,
    InventoryResposabilityAgreementLocationDTO,
    AnalyticalReportRawDataDTO
)


class AssetInventoryResponsibilityReportService:
    def __init__(self, database: AsyncIOMotorDatabase):
        self.db = database

    async def create_inventory_responsibility_agreement_report(
        self,
        parent_location_ids: Optional[List[str]]
    ) -> UploadFile:

        data = await self._build_data(parent_location_ids)
        env = Environment(
            loader=FileSystemLoader("app/template"),
            autoescape=True
        )
        template = env.get_template(
            "report/inventory_responsibility_agreement/report.html"
        )
        html_content = template.render(
            data=data,
            generated_at=time_now().strftime("%d/%m/%Y %H:%M")
        )

        pdf_bytes = BytesIO()
        HTML(string=html_content).write_pdf(pdf_bytes)
        pdf_bytes.seek(0)

        return UploadFile(
            filename="termo_responsabilidade_inventario.pdf",
            file=BytesIO(pdf_bytes.read())
        )

    async def _build_data(
        self,
        parent_location_ids: Optional[List[str]]
    ) -> List[InventoryResposabilityAgreementLocationDTO]:

        locations_ids = await self._get_all_descendant_locations(parent_location_ids)
        item_docs = await self.db.inventory_items.aggregate([
            {
                "$match": {
                    "parent_id": {"$in": locations_ids}
                }
            },
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
        ]).to_list(None)

        location_map = {
            location_doc["_id"]: InventoryResposabilityAgreementLocationDTO(
                path=" -> ".join(location_doc.get("path", [])),
                reference=location_doc.get("reference", None),
                level=location_doc.get("level", None)
            )
            for location_doc in (
                await self.db.inventory_items.find(
                    {"_id": {"$in": locations_ids}},
                    {"_id": 1, "path": 1, "reference": 1, "level": 1}
                ).to_list(None)
            )
        }

        item_map = {
            item_doc["_id"]: item_doc 
            for item_doc in item_docs
        }

        for item_doc in item_docs:
            parent = None
            parent_id = item_doc.get("parent_id")

            if parent_id and parent_id in item_map:
                parent = item_map[parent_id]

            location = location_map.get(item_doc.get("root_loc"))
            if not location:
                continue

            level = (
                item_doc.get("level") - location.level
                if parent
                else 1
            )

            photo_key = item_doc.get("photos")[0] if item_doc.get("photos", None) else None
            location.items.append(
                InventoryResposabilityAgreementItemDTO(
                    reference=item_doc.get("reference", None),
                    checked=item_doc.get("checked", False),
                    description=item_doc.get("asset_data", {}).get("description"),
                    serial=item_doc.get("asset_data", {}).get("serial"),
                    model=item_doc.get("asset_data", {}).get("model"),
                    color=self.level_to_color(level),
                    photo_key=photo_key,
                    parent_reference=parent.get("reference") if parent else None                
                )
            )

        for location in location_map.values():
            location.items = self._sort_items_hierarchy(location.items)

        sorted_locations = sorted(
            location_map.values(),
            key=lambda loc: len(loc.items) == 0
        )

        await self._resolve_photos_parallel(sorted_locations)
        return list(sorted_locations)

    async def _resolve_photos_parallel(
        self,
        locations: List[InventoryResposabilityAgreementLocationDTO]
    ) -> None:

        semaphore = asyncio.Semaphore(6)

        async def resolve(item: InventoryResposabilityAgreementItemDTO):
            if not item.photo_key:
                return
            async with semaphore:
                try:
                    url = await storage_s3_retrieve_objects_url(item.photo_key)
                    item.photo_base64 = await download_file_base64(url)
                except Exception:
                    item.photo_base64 = None

        tasks = [
            resolve(item)
            for location in locations
            for item in location.items
            if item.photo_key
        ]

        if tasks:
            await asyncio.gather(*tasks)

    async def _get_all_descendant_locations(
        self,
        parent_location_ids: Optional[List[str]]
    ) -> List[ObjectId]:

        if not parent_location_ids:
            docs = await self.db.inventory_items.find(
                {"node_type": "LOCATION"}, 
                {"_id": 1}
            ).to_list(None)

            return [doc["_id"] for doc in docs]

        parent_location_object_ids = []
        for parent_location_id in parent_location_ids:
            if not ObjectId.is_valid(parent_location_id):
                raise ValueError(
                    f"Invalid parent_location_id sent '{parent_location_id}', can not be tranformed to ObjectId"
                )
            parent_location_object_ids.append(ObjectId(parent_location_id))

        docs = await self.db.inventory_items.aggregate([
            {"$match": {"_id": {"$in": parent_location_object_ids}}},
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
            {"$group": {"_id": "$descendants._id"}},
            {"$project": {"_id": 1}}
        ]).to_list(None)

        descendant_locations_ids = [doc["_id"] for doc in docs]
        return list(set(descendant_locations_ids + parent_location_object_ids))

    def level_to_color(self, level: int) -> str:
        if level == 1:
            return "#f8f9fa"

        hue = (level * 0.25) % 1.0  

        lightness = 0.95 - (level * 0.02)
        lightness = max(0.75, lightness)

        saturation = 0.35 if level <= 5 else 0.3

        r, g, b = hls_to_rgb(hue, lightness, saturation)
        color = "#{:02X}{:02X}{:02X}".format(int(r*255), int(g*255), int(b*255))
        return color

    def _sort_items_hierarchy(self, items: List[InventoryResposabilityAgreementItemDTO]) -> List[InventoryResposabilityAgreementItemDTO]:
        children_map: Dict[Optional[str], List[InventoryResposabilityAgreementItemDTO]] = {}
        for item in items:
            parent = item.parent_reference
            children_map.setdefault(parent, []).append(item)

        parents_set = {item.parent_reference for item in items if item.parent_reference is not None}

        def flatten(parent_id: Optional[str]):
            flat_list = []

            leaves = [item for item in children_map.get(parent_id, []) if item.reference not in parents_set]
            for leaf in leaves:
                flat_list.append(leaf)

            non_leaves = [item for item in children_map.get(parent_id, []) if item.reference in parents_set]
            for parent_item in non_leaves:
                flat_list.append(parent_item)
                flat_list.extend(flatten(parent_item.reference))

            return flat_list

        return flatten(None)

class AnalyticalReportService:
    def __init__(self, database: AsyncIOMotorDatabase):
        self.db = database

    async def create_analytical_report(
        self,
        parent_ids: Optional[List[str]]
    ) -> UploadFile:

        rows = await self._build_data(parent_ids)
        dataframe = pandas.DataFrame(rows)
        file_bytes = BytesIO()

        with pandas.ExcelWriter(file_bytes, engine='openpyxl') as writer:
            dataframe.to_excel(writer, index=False, sheet_name='Relatório')
            ws = writer.sheets['Relatório']

            header_fill = PatternFill(start_color='007BFF', end_color='007BFF', fill_type='solid')
            header_font = Font(color='FFFFFF', bold=True)

            for col_num, column_title in enumerate(dataframe.columns, 1):
                cell = ws[f'{get_column_letter(col_num)}1']
                cell.fill = header_fill
                cell.font = header_font

            for col_num, column in enumerate(dataframe.columns, 1):
                max_length = max(
                    dataframe[column].astype(str).map(len).max(),
                    len(column)
                )
                ws.column_dimensions[get_column_letter(col_num)].width = max_length + 2

        file_bytes.seek(0)

        return UploadFile(
            filename="relatorio_analitico.xlsx",
            file=BytesIO(file_bytes.read())
        )

    async def _build_data(
        self,
        parent_ids: Optional[List[str]]
    ) -> List[Dict[str, Any]]:

        raw_data = await self._get_raw_data(parent_ids)
        asset_keys = set()
        max_path_len = 0

        for item in raw_data:
            if item.path:
                max_path_len = max(max_path_len, len(item.path))
            if item.asset_data:
                asset_keys.update(item.asset_data.keys())

        rows: List[Dict[str, Any]] = []
        for item in raw_data:
            row: Dict[str, Any] = {}

            for index in range(max_path_len):
                col_name = f"PATH_{index+1}"
                path_value = None
                if item.path and index < len(item.path):
                    path_value = item.path[index]
                row[col_name] = path_value

            row["PLAQUETA"] = item.reference
            row["INVENTARIADO"] = "SIM" if item.checked else "NÃO"
            row["INVENTARIADO EM"] = item.checked_at.strftime("%d/%m/%Y %H:%M") if item.checked_at else None

            for key in asset_keys:
                key_name = key.upper()
                row[key_name] = item.asset_data.get(key) if item.asset_data else None

            rows.append(row)

        return rows        

    async def _get_raw_data(
        self,
        parent_ids: Optional[List[str]]
    ) -> List[AnalyticalReportRawDataDTO]:

        docs = []
        raw_fields = {
            field.name: 1
            for field in fields(AnalyticalReportRawDataDTO)
        }

        if not parent_ids:
            docs = await self.db.inventory_items.find(
                {"node_type": "ASSET"},
                raw_fields
            ).to_list(None)
        else:
            parent_object_ids = []
            for parent_id in parent_ids:
                if not ObjectId.is_valid(parent_id):
                    raise ValueError(
                        f"Invalid parent_id sent '{parent_id}', can not be tranformed to ObjectId"
                    )
                parent_object_ids.append(ObjectId(parent_id))

            docs = await self.db.inventory_items.aggregate(
                [
                    {"$match": {"_id": {"$in": parent_object_ids}}},
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
                    {"$match": {"descendants.node_type": "ASSET"}},
                    {"$replaceRoot": {"newRoot": "$descendants"}},
                    {"$project": {**raw_fields}}
                ]
            ).to_list(None)

        dto_list: List[AnalyticalReportRawDataDTO] = [
            AnalyticalReportRawDataDTO(**doc) for doc in docs
        ]

        return dto_list