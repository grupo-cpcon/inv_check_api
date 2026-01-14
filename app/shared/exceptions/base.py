class AppError(Exception):
    status_code: int = 400
    error_code: str = "APP_ERROR"

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message
