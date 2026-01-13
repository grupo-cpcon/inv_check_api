from app.shared.exceptions.base import AppError

class StorageError(AppError):
    error_code = "STORAGE_ERROR"
