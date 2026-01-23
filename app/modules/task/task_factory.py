from app.modules.task.task_choices import AsyncTaskResultType, AsyncTaskType
from app.modules.task.handlers.export_analytical_report_handler import ExportAnalyticalReportHandler
from app.modules.task.task_schemas import AsyncTaskSpec


class AsyncTaskFactory:
    _registry = {
        AsyncTaskType.EXPORT_ANALYTICAL: AsyncTaskSpec(
            handler=ExportAnalyticalReportHandler,
            result_type=AsyncTaskResultType.ARCHIVE
        )
    }

    @classmethod
    def get_spec(cls, task_type: AsyncTaskType) -> AsyncTaskSpec:
        spec = cls._registry.get(task_type)
        if not spec:
            raise ValueError(f"Task type não registrada: {task_type}")
        return spec