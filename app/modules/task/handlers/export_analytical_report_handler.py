from app.modules.report.report_repository import ReportAnaliticalService
from app.modules.task.handlers.base_handler import BaseAsyncTaskHandler
from typing import Dict, Any

class ExportAnalyticalReportHandler(BaseAsyncTaskHandler):
    async def execute(self, params: Dict[Any, Any]):
        service = ReportAnaliticalService(self.db)
        return await service.create_analitical_report(
            parent_location_ids=params["parent_ids"]
        )
