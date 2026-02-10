from app.modules.task.task_choices import AsyncTaskResultType, AsyncTaskType
from app.modules.task.handlers.export.export_inventory_respponsability_agreement_report_handler import ExportInventoryResponsibilityAgreementReportHandler
from app.modules.task.handlers.export.export_analytical_report_handler import ExportAnalyticalReportHandler
from app.modules.task.handlers.export.export_images_handler import ExportImagesHandler
from app.modules.task.handlers.upload.upload_items_images_handler import UploadItemsImagesHandler
from app.modules.task.task_schemas import AsyncTaskSpec


class AsyncTaskFactory:
    _registry = {
        AsyncTaskType.EXPORT_INVENTORY_RESPONSIBILITY_AGREEMENT_REPORT: AsyncTaskSpec(
            handler=ExportInventoryResponsibilityAgreementReportHandler,
            result_type=AsyncTaskResultType.ARCHIVE
        ),
        AsyncTaskType.EXPORT_ANALYTICAL_REPORT: AsyncTaskSpec(
            handler=ExportAnalyticalReportHandler,
            result_type=AsyncTaskResultType.ARCHIVE
        ),
        AsyncTaskType.EXPORT_ITEMS_IMAGES: AsyncTaskSpec(
            handler=ExportImagesHandler,
            result_type=AsyncTaskResultType.TEMPORARY_URL_ACCESS
        ),
        AsyncTaskType.UPLOAD_ITEMS_IMAGES: AsyncTaskSpec(
            handler=UploadItemsImagesHandler,
            result_type=AsyncTaskResultType.RAW_RESULT
        )
    }

    @classmethod
    def get_spec(cls, task_type: AsyncTaskType) -> AsyncTaskSpec:
        spec = cls._registry.get(task_type)
        if not spec:
            raise ValueError(f"Task type não registrada: {task_type}")
        return spec