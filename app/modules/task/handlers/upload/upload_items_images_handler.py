from app.modules.task.handlers.base_handler import BaseAsyncTaskHandler
from app.modules.upload_control.upload_control_repository import UploadItemsImages
from typing import Dict, Any

class UploadItemsImagesHandler(BaseAsyncTaskHandler):
    async def execute(self, params: Dict[Any, Any]):
        service = UploadItemsImages(self.db)
        return await service.perform_upload(
            encoded_file=params["encoded_file"]
        )
