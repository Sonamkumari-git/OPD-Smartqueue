"""Safe operational errors that never leak stack traces to clients."""
from fastapi import status


class AppError(Exception):
    def __init__(self, message: str, error_code: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        super().__init__(message)


class NotFoundError(AppError):
    def __init__(self, message: str = "Resource not found."):
        super().__init__(message, "NOT_FOUND", status.HTTP_404_NOT_FOUND)


class ForbiddenError(AppError):
    def __init__(self, message: str = "You are not authorized to perform this action."):
        super().__init__(message, "FORBIDDEN", status.HTTP_403_FORBIDDEN)


class ConflictError(AppError):
    def __init__(self, message: str):
        super().__init__(message, "CONFLICT", status.HTTP_409_CONFLICT)
