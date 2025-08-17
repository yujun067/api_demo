from typing import Any
from pydantic import BaseModel, Field, ConfigDict


class StandardErrorResponse(BaseModel):
    """Standard error response format for all API errors."""
    
    error: str = Field(..., description="Human-readable error message")
    error_code: str = Field(..., description="Machine-readable error code")
    details: Any = Field(None, description="Additional error details")
    timestamp: str = Field(..., description="ISO 8601 timestamp")
    path: str = Field(..., description="Request path")
    method: str = Field(..., description="HTTP method")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "error": "Resource not found",
            "error_code": "NOT_FOUND",
            "details": "User with ID 123 not found",
            "timestamp": "2024-01-01T00:00:00Z",
            "path": "/api/v1/users/123",
            "method": "GET"
        }
    })
