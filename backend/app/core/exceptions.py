import logging
import uuid
from datetime import datetime, timezone
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

class AppException(Exception):
    """Base application exception."""
    def __init__(self, message: str, status_code: int = 500, code: str = "INTERNAL_ERROR"):
        self.message = message
        self.status_code = status_code
        self.code = code
        super().__init__(message)

class EntityNotFoundException(AppException):
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message=message, status_code=404, code="NOT_FOUND")

class DatabaseException(AppException):
    def __init__(self, message: str = "Database operation failed"):
        super().__init__(message=message, status_code=503, code="DATABASE_ERROR")

class ProviderException(AppException):
    def __init__(self, message: str = "External provider error", status_code: int = 502):
        super().__init__(message=message, status_code=status_code, code="PROVIDER_ERROR")

class ValidationException(AppException):
    def __init__(self, message: str = "Validation error"):
        super().__init__(message=message, status_code=400, code="VALIDATION_ERROR")

def register_exception_handlers(app: FastAPI):
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        request_id = str(uuid.uuid4())
        logger.error(f"[{request_id}] {exc.code}: {exc.message} on {request.method} {request.url.path}")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "request_id": request_id,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            }
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        request_id = str(uuid.uuid4())
        logger.error(f"[{request_id}] Unexpected error on {request.method} {request.url.path}: {exc}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An internal error occurred. Please try again later.",
                    "request_id": request_id,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            }
        )
