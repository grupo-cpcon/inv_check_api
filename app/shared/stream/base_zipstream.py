import zipstream
from abc import ABC, abstractmethod
from typing import Any
from app.shared.storage.s3.multi_part_uploader import MultipartUploader


class BaseStreamingZipWriter(ABC):
    def __init__(self, uploader: MultipartUploader):
        self.uploader = uploader
        self.zs = zipstream.ZipStream()

    @abstractmethod
    async def process(self, *args, **kwargs) -> Any:
        raise NotImplementedError

    async def stream_to_cloud(self):
        await self.uploader.start()

        for chunk in self.zs:
            await self.uploader.write(chunk)

        return await self.uploader.finish()