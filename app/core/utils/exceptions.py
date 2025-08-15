from datetime import datetime, timezone
from typing import Any
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from ..config.logging import get_logger
from app.core.config.settings import settings
from app.models.common import StandardErrorResponse

logger = get_logger("exceptions")
IS_PROD = settings.app_env.lower() == "prod"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _default_error_code(status_code: int) -> str:
    mapping = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
        409: "CONFLICT",
        422: "VALIDATION_ERROR",
        500: "INTERNAL_ERROR",
    }
    return mapping.get(status_code, "UNKNOWN_ERROR")


class AppException(HTTPException):
    def __init__(
        self, status_code: int, error_code: str, message: str, details: Any = None, headers: dict | None = None
    ):
        super().__init__(
            status_code=status_code,
            detail={"error": message, "error_code": error_code, "details": details},
            headers=headers,
        )


class ValidationException(AppException):
    def __init__(self, details: Any = None):
        super().__init__(400, "VALIDATION_ERROR", "Validation error", details)


class NotFoundException(AppException):
    def __init__(self, resource: str, resource_id: str):
        super().__init__(
            404, "NOT_FOUND", f"{resource} not found", details=f"{resource} with ID {resource_id} not found"
        )

class InternalServerException(AppException):
    def __init__(self, details: str | None = None):
        super().__init__(500, "INTERNAL_ERROR", "Internal server error", details)


class UnauthorizedException(AppException):
    def __init__(self, details: str | None = None):
        super().__init__(401, "UNAUTHORIZED", "Unauthorized access", details)


class ForbiddenException(AppException):
    def __init__(self, details: str | None = None):
        super().__init__(403, "FORBIDDEN", "Access forbidden", details)


class ConflictException(AppException):
    def __init__(self, resource: str, details: str | None = None):
        super().__init__(409, "CONFLICT", f"{resource} conflict", details)


class RateLimitException(AppException):
    def __init__(self, details: str | None = None):
        super().__init__(429, "RATE_LIMIT_EXCEEDED", "Rate limit exceeded", details)


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle HTTP exceptions with standardized response format."""
    if isinstance(exc.detail, dict):
        error_details = exc.detail.get("details")
        error_message = exc.detail.get("error", "Error")
        error_code = exc.detail.get("error_code", _default_error_code(exc.status_code))
    else:
        error_details = None
        error_message = str(exc.detail) if exc.detail else "Error"
        error_code = _default_error_code(exc.status_code)
    
    error_response = StandardErrorResponse(
        error=error_message,
        error_code=error_code,
        details=error_details,
        timestamp=_utc_now_iso(),
        path=request.url.path,
        method=request.method
    )
    
    return JSONResponse(
        status_code=exc.status_code, 
        content=error_response.model_dump(),
        headers=getattr(exc, "headers", None) or None
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle validation exceptions with standardized response format."""
    error_response = StandardErrorResponse(
        error="Validation error",
        error_code="VALIDATION_ERROR",
        details=exc.errors(),
        timestamp=_utc_now_iso(),
        path=request.url.path,
        method=request.method
    )
    
    return JSONResponse(
        status_code=422,  # Use 422 for validation errors (RFC 4918)
        content=error_response.model_dump()
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle general exceptions with standardized response format."""
    # Log the full stack trace
    logger.exception(f"Unhandled exception: {exc}")
    
    error_response = StandardErrorResponse(
        error="Internal server error",
        error_code="INTERNAL_ERROR",
        details=None if IS_PROD else str(exc),
        timestamp=_utc_now_iso(),
        path=request.url.path,
        method=request.method
    )
    
    return JSONResponse(
        status_code=500,
        content=error_response.model_dump()
    )


def setup_exception_handlers(app):
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)
