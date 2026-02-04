from app.modules.report.report_repository import ImagesExportService
from app.modules.task.handlers.base_handler import BaseAsyncTaskHandler
from typing import Dict, Any

class ExportImagesHandler(BaseAsyncTaskHandler):
    async def execute(self, params: Dict[Any, Any]):
        service = ImagesExportService(self.db)
        return await service.export_images(
            parent_id=params["parent_id"],
            mode=params["mode"]
        )