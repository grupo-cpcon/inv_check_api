import base64
from typing import List

from app.shared.stream.base_zipstream import BaseStreamingZipWriter
from app.shared.files.images import detect_image_extension
import zipstream


class ImageStreamingZipWriter(BaseStreamingZipWriter):
    async def process(
        self,
        folder: str,
        reference: str,
        images_base64: List[str]
    ) -> None:
        need_index = len(images_base64) > 1

        for idx, photo_base64 in enumerate(images_base64, start=1):
            image_bytes = base64.b64decode(photo_base64)
            ext = detect_image_extension(image_bytes)

            filename = (
                f"{reference}.{ext}"
                if not need_index
                else f"{reference}-{idx}.{ext}"
            )

            path = f"{folder}/{filename}"

            self.zs.add(
                image_bytes,
                path
            )