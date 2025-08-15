from typing import Optional, List
from pydantic import BaseModel, Field, field_validator
from datetime import datetime


class HackerNewsItemResponse(BaseModel):
    """Pydantic model for Hacker News item API response."""

    id: int = Field(..., description="Unique identifier for the item")
    title: str = Field(..., description="Title of the item")
    url: Optional[str] = Field(None, description="URL of the item")
    score: int = Field(..., description="Score/points of the item")
    author: str = Field(..., description="Username of the author")
    timestamp: int = Field(..., description="Unix timestamp when the item was created")
    descendants: Optional[int] = Field(None, description="Number of comments")
    kids: Optional[List[int]] = Field(None, description="List of comment IDs")
    type: str = Field(..., description="Type of item (story, comment, etc.)")
    text: Optional[str] = Field(None, description="Text content for text posts")

    class Config:
        from_attributes = True


class FetchRequest(BaseModel):
    """Model for fetch request parameters."""

    min_score: Optional[int] = Field(None, ge=0, description="Minimum score filter")
    keyword: Optional[str] = Field(None, min_length=1, description="Keyword filter for title")
    limit: Optional[int] = Field(100, ge=1, le=500, description="Number of items to fetch")

    class Config:
        json_schema_extra = {"example": {"min_score": 50, "keyword": "AI", "limit": 100}}


class FetchResponse(BaseModel):
    """Model for fetch response."""

    task_id: str = Field(..., description="Unique task identifier")
    status: str = Field(..., description="Task status")
    message: str = Field(..., description="Status message")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "uuid-string",
                "status": "accepted",
                "message": "Data fetching job started",
                "timestamp": "2024-01-01T00:00:00Z",
            }
        }





class DataQueryParams(BaseModel):
    """Query parameters for data endpoint with automatic validation"""

    item_id: Optional[int] = Field(None, description="Get specific item by ID")
    min_score: Optional[int] = Field(None, ge=0, description="Filter by minimum score")
    keyword: Optional[str] = Field(None, description="Filter by keyword in title")
    order_by: str = Field("score", description="Order by field (score, time, id)")
    order_direction: str = Field("desc", description="Order direction (asc, desc)")

    @field_validator("keyword")
    @classmethod
    def validate_keyword(cls, v):
        if v is not None and v.strip() == "":
            return None
        return v

    @field_validator("order_by")
    @classmethod
    def validate_order_by(cls, v):
        if v not in ["score", "time", "id"]:
            raise ValueError("order_by must be one of: score, time, id")
        return v

    @field_validator("order_direction")
    @classmethod
    def validate_order_direction(cls, v):
        if v not in ["asc", "desc"]:
            raise ValueError("order_direction must be one of: asc, desc")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "item_id": 12345,
                "min_score": 100,
                "keyword": "python",
                "order_by": "score",
                "order_direction": "desc",
            }
        }
