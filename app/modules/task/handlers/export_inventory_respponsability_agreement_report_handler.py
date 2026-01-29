from app.modules.report.report_repository import AssetInventoryResponsibilityReportService
from app.modules.task.handlers.base_handler import BaseAsyncTaskHandler
from typing import Dict, Any

class ExportInventoryResponsibilityAgreementReportHandler(BaseAsyncTaskHandler):
    async def execute(self, params: Dict[Any, Any]):
        service = AssetInventoryResponsibilityReportService(self.db)
        return await service.create_inventory_responsibility_agreement_report(
            parent_location_ids=params["parent_location_ids"]
        )
