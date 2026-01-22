from enum import Enum

# class AsyncTaskStatus(str, Enum):
#     PENDING = "PENDING"
#     IN_PROGRESS = "IN_PROGRESS"
#     SUCCESS = "SUCCESS"
#     ERROR = "ERROR"

class AsyncTaskStatus(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class AsyncTaskResultType(str, Enum):
    ARCHIVE = "ARCHIVE"
    RAW_RESULT = "RAW_RESULT"