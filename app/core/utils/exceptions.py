from datetime import datetime, timezone
from typing import Any
import http
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from ..config.logging import get_logger
from app.models.common import StandardErrorResponse

logger = get_logger("exceptions")


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _default_error_code(status_code: int) -> str:
    """Get default error code based on HTTP status code."""
    try:
        # Use Python's built-in HTTP status descriptions
        http_status = http.HTTPStatus(status_code)
        # Convert phrase to uppercase and replace spaces with underscores
        return http_status.phrase.upper().replace(" ", "_")
    except ValueError:
        # Fallback for unknown status codes
        return "UNKNOWN_ERROR"


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
        super().__init__(status.HTTP_400_BAD_REQUEST, "BAD_REQUEST", "Validation error", details)


class NotFoundException(AppException):
    def __init__(self, resource: str, resource_id: str):
        super().__init__(
            status.HTTP_404_NOT_FOUND, "NOT_FOUND", f"{resource} not found", 
            details=f"{resource} with ID {resource_id} not found"
        )


class InternalServerException(AppException):
    def __init__(self, details: str | None = None):
        super().__init__(status.HTTP_500_INTERNAL_SERVER_ERROR, "INTERNAL_SERVER_ERROR", "Internal server error", details)


class UnauthorizedException(AppException):
    def __init__(self, details: str | None = None):
        super().__init__(status.HTTP_401_UNAUTHORIZED, "UNAUTHORIZED", "Unauthorized access", details)


class ForbiddenException(AppException):
    def __init__(self, details: str | None = None):
        super().__init__(status.HTTP_403_FORBIDDEN, "FORBIDDEN", "Access forbidden", details)


class ConflictException(AppException):
    def __init__(self, resource: str, details: str | None = None):
        super().__init__(status.HTTP_409_CONFLICT, "CONFLICT", f"{resource} conflict", details)


class RateLimitException(AppException):
    def __init__(self, details: str | None = None):
        super().__init__(status.HTTP_429_TOO_MANY_REQUESTS, "TOO_MANY_REQUESTS", "Rate limit exceeded", details)


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
        error_code="UNPROCESSABLE_ENTITY",
        details=exc.errors(),
        timestamp=_utc_now_iso(),
        path=request.url.path,
        method=request.method
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,  # Use 422 for validation errors (RFC 4918)
        content=error_response.model_dump()
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle general exceptions with standardized response format."""
    # Log the full stack trace
    logger.exception(f"Unhandled exception: {exc}")
    
    error_response = StandardErrorResponse(
        error="Internal server error",
        error_code="INTERNAL_SERVER_ERROR",
        details=str(exc),
        timestamp=_utc_now_iso(),
        path=request.url.path,
        method=request.method
    )
      
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response.model_dump()
    )


def setup_exception_handlers(app):
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)
