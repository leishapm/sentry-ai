from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from src.core.logging import get_logger

logger = get_logger(__name__)


class SentryException(Exception):
    """Base exception for SENTRY domain errors."""

    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Any = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details


class EntityNotFoundException(SentryException):
    """Resource or entity not found error."""

    def __init__(self, message: str = "Requested resource not found.", details: Any = None) -> None:
        super().__init__(
            message=message,
            code="NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            details=details,
        )


class InvalidOperationException(SentryException):
    """Invalid client request or state transition error."""

    def __init__(self, message: str, details: Any = None) -> None:
        super().__init__(
            message=message,
            code="BAD_REQUEST",
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details,
        )


def setup_exception_handlers(app: FastAPI) -> None:
    """Register custom exception handlers on FastAPI app."""

    @app.exception_handler(SentryException)
    async def sentry_exception_handler(request: Request, exc: SentryException) -> JSONResponse:
        logger.warning(
            "Sentry domain exception",
            extra={"path": request.url.path, "code": exc.code, "message": exc.message},
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "details": exc.details,
                }
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        logger.warning(
            "Request validation error",
            extra={"path": request.url.path, "errors": exc.errors()},
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Invalid request payload or parameters.",
                    "details": exc.errors(),
                }
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.error(
            "Unhandled server exception",
            exc_info=exc,
            extra={"path": request.url.path},
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected error occurred. Please try again later.",
                    "details": None,
                }
            },
        )
