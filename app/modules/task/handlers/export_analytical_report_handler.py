from app.modules.report.report_repository import AnalyticalReportService
from app.modules.task.handlers.base_handler import BaseAsyncTaskHandler
from typing import Dict, Any

class ExportAnalyticalReportHandler(BaseAsyncTaskHandler):
    async def execute(self, params: Dict[Any, Any]):
        service = AnalyticalReportService(self.db)
        return await service.create_analytical_report(
            parent_ids=params["parent_ids"]
        )
