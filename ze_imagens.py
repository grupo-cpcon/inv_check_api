import asyncio
import base64
import zipfile
from io import BytesIO
from typing import List, Dict
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

from app.shared.storage.s3.objects import storage_s3_retrieve_objects_url
from app.shared.storage.utils import download_file_base64
import os

load_dotenv()

MONGO_URL = "mongodb://admin:Admin123456@138.197.106.154:27017"

_client = AsyncIOMotorClient(
    MONGO_URL,
    maxPoolSize=50,
    minPoolSize=10,
    maxIdleTimeMS=30000,
    serverSelectionTimeoutMS=5000
)

_database = _client["cp_vtal_-_75547"]
_collection = _database["inventory_items"]


async def collect_all_locations() -> List[str]:
    docs = await _collection.find(
        {"node_type": "LOCATION"},
        {"_id": 1}
    ).to_list(None)
    return [doc["_id"] for doc in docs]

async def build_data() -> Dict[str, dict]:

    locations_ids = await collect_all_locations()
    item_docs = await _collection.aggregate([
        {
            "$match": {
                "parent_id": { "$in": locations_ids },
                "node_type": { "$ne": "LOCATION" }
            }
        },
        {
            "$graphLookup": {
            "from": "inventory_items",
            "startWith": "$_id",
            "connectFromField": "_id",
            "connectToField": "parent_id",
            "as": "descendants",
            "restrictSearchWithMatch": {
                    "node_type": { "$ne": "LOCATION" }
                }
            }
        },
        { "$addFields": { "root_loc": "$parent_id" } },
        {
            "$project": {
                "docs": { "$concatArrays": [["$$ROOT"], "$descendants"] },
                "root_loc": 1
            }
        },
        { "$unwind": "$docs" },
        { "$addFields": { "docs.root_loc": "$root_loc" } },
        { "$replaceRoot": { "newRoot": "$docs" } },
        {
            "$match": {
                "photos": { "$exists": True, "$ne": [] }
            }
        },
        { "$project": { "descendants": 0 } }
    ]).to_list(None)

    location_docs = await _collection.find(
        {"_id": {"$in": locations_ids}},
        {"_id": 1, "path": 1}
    ).to_list(None)

    locations: Dict[str, dict] = {
        str(loc["_id"]): {
            "path": " -> ".join(loc.get("path", [])),
            "items": []
        }
        for loc in location_docs
    }

    for item in item_docs:
        loc = locations.get(str(item["root_loc"]))
        if not loc:
            continue

        loc["items"].append({
            "reference": item.get("reference"),
            "photo_keys": item.get("photos", []),
            "photos": []
        })

    filtered_locations = [
        loc
        for loc in locations.values()
        if loc.get("items")
    ]

    await resolve_photos_parallel(filtered_locations)
    return filtered_locations

async def resolve_photos_parallel(locations: list) -> None:
    semaphore = asyncio.Semaphore(10)
    tasks = []

    async def resolve(item: dict, photo_key: str):
        print(photo_key)
        async with semaphore:
            try:
                url = await storage_s3_retrieve_objects_url(photo_key)
                print(url)
                base64_img = await download_file_base64(url)
                item["photos"].append(base64_img)
            except Exception as e:
                print(e)
                pass

    for location in locations:
        for item in location["items"]:
            for photo_key in item["photo_keys"]:
                tasks.append(resolve(item, photo_key))

    if tasks:
        await asyncio.gather(*tasks)

def detect_image_extension(image_bytes: bytes) -> str:
    if image_bytes.startswith(b"\xff\xd8\xff"):
        return "jpg"
    if image_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if image_bytes.startswith(b"GIF87a") or image_bytes.startswith(b"GIF89a"):
        return "gif"
    if image_bytes.startswith(b"RIFF") and b"WEBP" in image_bytes[8:16]:
        return "webp"
    return "bin"

async def build_zip(locations: list) -> BytesIO:
    zip_buffer = BytesIO()

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
        for location in locations:
            folder = location["path"] or "SEM_LOCALIZACAO"

            for item in location["items"]:
                need_index = len(item["photos"]) > 1
                ref = item["reference"] or "SEM_REFERENCIA"

                for idx, photo_base64 in enumerate(item["photos"], start=1):
                    image_bytes = base64.b64decode(photo_base64)
                    ext = detect_image_extension(image_bytes)

                    filename = (
                        f"{ref}.{ext}"
                        if not need_index
                        else f"{ref}-{idx}.{ext}"
                    )

                    zipf.writestr(f"{folder}/{filename}", image_bytes)

    zip_buffer.seek(0)
    return zip_buffer

async def main():
    data = await build_data()
    zip_file = await build_zip(data)

    os.makedirs("./results", exist_ok=True)
    full_path = os.path.join("./results", "inventario_fotos.zip")

    with open(full_path, "wb") as f:
        f.write(zip_file.read())

asyncio.run(main())