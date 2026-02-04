import asyncio
from io import BytesIO
from typing import List, Dict, Any
import boto3
from app.shared.storage.s3.client import get_s3_client
import os
from app.shared.storage.s3.objects import storage_s3_retrieve_objects_url


class MultipartUploader:
    def __init__(
        self,
        key: str,
        part_size: int = 5 * 1024 * 1024
    ):
        self.key = key
        self.s3 = get_s3_client()
        self.bucket = os.getenv("AWS_S3_BUCKET")
        self.part_size = part_size

        self.parts: List[Dict[str, Any]] = []
        self.part_number = 1
        self.buffer = BytesIO()
        self.upload_id: str | None = None

        self._loop = asyncio.get_running_loop()

    async def start(self):
        resp = await self._loop.run_in_executor(
            None,
            lambda: self.s3.create_multipart_upload(
                Bucket=self.bucket,
                Key=self.key,
                ContentType="application/zip"
            )
        )
        self.upload_id = resp["UploadId"]

    async def write(self, data: bytes):
        self.buffer.write(data)

        if self.buffer.tell() >= self.part_size:
            await self._flush()

    async def _flush(self):
        self.buffer.seek(0)
        data = self.buffer.read()

        resp = await self._loop.run_in_executor(
            None,
            lambda: self.s3.upload_part(
                Bucket=self.bucket,
                Key=self.key,
                UploadId=self.upload_id,
                PartNumber=self.part_number,
                Body=data
            )
        )

        self.parts.append({
            "PartNumber": self.part_number,
            "ETag": resp["ETag"]
        })

        self.part_number += 1
        self.buffer = BytesIO()

    async def finish(self):
        if self.buffer.tell() > 0:
            await self._flush()

        await self._loop.run_in_executor(
            None,
            lambda: self.s3.complete_multipart_upload(
                Bucket=self.bucket,
                Key=self.key,
                UploadId=self.upload_id,
                MultipartUpload={"Parts": self.parts}
            )
        )