import base64
import zipfile
import io
import re
from typing import Optional, List, Dict, Tuple
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.modules.item.item_storage_paths import ItemStoragePaths
from app.modules.item.item_repository import ItemRepository
from fastapi import UploadFile
from app.shared.files.images import detect_image_extension

class UploadItemsImages:
    def __init__(self, database: AsyncIOMotorDatabase):
        self.db = database
        self._collection = self.db["inventory_items"]
        self._cache: Dict[Tuple[str, str], dict] = {}

    async def _find_asset_by_reference_and_path(self, reference: str, location_path: List[str]):
        key = (reference, " -> ".join(location_path))
        if key in self._cache:
            return self._cache[key]

        candidates = await self._collection.find(
            {"reference": reference, "node_type": "ASSET"}
        ).to_list(None)

        for item in candidates:
            current = item
            locations_in_path = []

            while current.get("parent_id"):
                parent = await self._collection.find_one({"_id": current["parent_id"]})
                if not parent:
                    break

                if parent["node_type"] == "LOCATION":
                    locations_in_path.insert(0, parent["reference"])

                current = parent

            locations_in_path = " -> ".join(locations_in_path)
            if locations_in_path == location_path:
                self._cache[key] = item
                return item

        self._cache[key] = None
        return None

    async def perform_upload(self, encoded_file: str):
        try:
            file_bytes = base64.b64decode(encoded_file)
        except Exception:
            raise ValueError("Erro ao processar arquivo")

        zip_file = io.BytesIO(file_bytes)
        reference_regex = re.compile(r"(?P<reference>.+?)(?:-(?P<num>\d+))?\.\w+$")

        with zipfile.ZipFile(zip_file) as z:
            for file_info in z.infolist():
                if file_info.is_dir():
                    continue

                path_parts = file_info.filename.strip("/").split("/")
                if len(path_parts) < 2:
                    continue

                location_path = path_parts[0]
                file_name = path_parts[-1]
                match = reference_regex.match(file_name)
                if not match:
                    continue

                reference = match.group("reference")
                item = await self._find_asset_by_reference_and_path(reference, location_path)
                if not item:
                    continue

                with z.open(file_info.filename) as f:
                    try:
                        image_bytes = f.read()
                    except Exception:
                        continue

                file_like = io.BytesIO(image_bytes)
                upload_file = UploadFile(filename="image", file=file_like)

                base_item_path = ItemStoragePaths(
                    client_name=self.db.name,
                    item_id=item["_id"]
                ).images

                item_photo_path = await ItemRepository().perform_save_item_photos([upload_file], base_item_path)

                if item_photo_path:
                    await self._collection.update_one(
                        {"_id": item["_id"]},
                        {
                            "$push": {
                                "photos": item_photo_path[0]
                            }
                        }
                    )