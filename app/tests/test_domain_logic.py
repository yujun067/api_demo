import pytest
from datetime import datetime, timezone
from app.models.schemas import (
    HackerNewsItemResponse, 
    FetchRequest, 
    FetchResponse, 
    DataQueryParams
)
from app.services.hacker_news_client import HackerNewsAPIClient


class TestHackerNewsItemResponse:
    """Test domain logic for HackerNewsItemResponse model."""
    
    def test_valid_item_response(self):
        """Test creating a valid HackerNewsItemResponse."""
        item_data = {
            "id": 12345,
            "title": "Test Story",
            "url": "https://example.com",
            "score": 100,
            "author": "testuser",
            "timestamp": 1640995200,
            "descendants": 10,
            "type": "story",
            "text": None
        }
        
        item = HackerNewsItemResponse(**item_data)
        
        assert item.id == 12345
        assert item.title == "Test Story"
        assert item.url == "https://example.com"
        assert item.score == 100
        assert item.author == "testuser"
        assert item.timestamp == 1640995200
        assert item.descendants == 10
        assert item.type == "story"
        assert item.text is None
    
    def test_item_response_without_optional_fields(self):
        """Test creating item response with minimal required fields."""
        item_data = {
            "id": 12345,
            "title": "Test Story",
            "score": 100,
            "author": "testuser",
            "timestamp": 1640995200,
            "type": "story"
        }
        
        item = HackerNewsItemResponse(**item_data)
        
        assert item.id == 12345
        assert item.title == "Test Story"
        assert item.url is None
        assert item.descendants is None
        assert item.text is None


class TestFetchRequest:
    """Test domain logic for FetchRequest model."""
    
    def test_valid_fetch_request(self):
        """Test creating a valid FetchRequest."""
        request_data = {
            "min_score": 50,
            "keyword": "AI",
            "limit": 100
        }
        
        request = FetchRequest(**request_data)
        
        assert request.min_score == 50
        assert request.keyword == "AI"
        assert request.limit == 100
    
    def test_fetch_request_with_defaults(self):
        """Test FetchRequest with default values."""
        request = FetchRequest()
        
        assert request.min_score is None
        assert request.keyword is None
        assert request.limit == 100
    
    def test_fetch_request_validation_min_score(self):
        """Test min_score validation."""
        with pytest.raises(ValueError):
            FetchRequest(min_score=-1)
    
    def test_fetch_request_validation_limit_min(self):
        """Test limit minimum validation."""
        with pytest.raises(ValueError):
            FetchRequest(limit=0)
    
    def test_fetch_request_validation_limit_max(self):
        """Test limit maximum validation."""
        with pytest.raises(ValueError):
            FetchRequest(limit=501)
    
    def test_fetch_request_validation_keyword_min_length(self):
        """Test keyword minimum length validation."""
        with pytest.raises(ValueError):
            FetchRequest(keyword="")


class TestFetchResponse:
    """Test domain logic for FetchResponse model."""
    
    def test_valid_fetch_response(self):
        """Test creating a valid FetchResponse."""
        timestamp = datetime.now(timezone.utc)
        response_data = {
            "task_id": "test-task-123",
            "status": "accepted",
            "message": "Data fetching job started",
            "timestamp": timestamp
        }
        
        response = FetchResponse(**response_data)
        
        assert response.task_id == "test-task-123"
        assert response.status == "accepted"
        assert response.message == "Data fetching job started"
        assert response.timestamp == timestamp
    
    def test_fetch_response_with_default_timestamp(self):
        """Test FetchResponse with default timestamp."""
        response_data = {
            "task_id": "test-task-123",
            "status": "accepted",
            "message": "Data fetching job started"
        }
        
        response = FetchResponse(**response_data)
        
        assert response.task_id == "test-task-123"
        assert response.status == "accepted"
        assert response.message == "Data fetching job started"
        assert isinstance(response.timestamp, datetime)


class TestDataQueryParams:
    """Test domain logic for DataQueryParams model."""
    
    def test_valid_data_query_params(self):
        """Test creating valid DataQueryParams."""
        params_data = {
            "item_id": 12345,
            "min_score": 100,
            "keyword": "python",
            "order_by": "score",
            "order_direction": "desc"
        }
        
        params = DataQueryParams(**params_data)
        
        assert params.item_id == 12345
        assert params.min_score == 100
        assert params.keyword == "python"
        assert params.order_by == "score"
        assert params.order_direction == "desc"
    
    def test_data_query_params_with_defaults(self):
        """Test DataQueryParams with default values."""
        params = DataQueryParams()
        
        assert params.item_id is None
        assert params.min_score is None
        assert params.keyword is None
        assert params.order_by == "score"
        assert params.order_direction == "desc"
    
    def test_data_query_params_validation_min_score(self):
        """Test min_score validation."""
        with pytest.raises(ValueError):
            DataQueryParams(min_score=-1)
    
    def test_data_query_params_validation_order_by(self):
        """Test order_by validation."""
        with pytest.raises(ValueError):
            DataQueryParams(order_by="invalid")
    
    def test_data_query_params_validation_order_direction(self):
        """Test order_direction validation."""
        with pytest.raises(ValueError):
            DataQueryParams(order_direction="invalid")
    
    def test_data_query_params_keyword_validation_empty_string(self):
        """Test keyword validation for empty string."""
        params = DataQueryParams(keyword="   ")
        assert params.keyword is None
    
    def test_data_query_params_keyword_validation_whitespace(self):
        """Test keyword validation for whitespace-only string."""
        params = DataQueryParams(keyword="  \t\n  ")
        assert params.keyword is None


class TestHackerNewsClientFiltering:
    """Test domain logic for item filtering (pure business logic)."""
    
    def test_filter_items_by_min_score(self):
        """Test filtering items by minimum score."""
        client = HackerNewsAPIClient()
        
        items = [
            {"id": 1, "title": "Story 1", "score": 50},
            {"id": 2, "title": "Story 2", "score": 100},
            {"id": 3, "title": "Story 3", "score": 150},
        ]
        
        filtered = client.filter_items(items, min_score=100)
        
        assert len(filtered) == 2
        assert filtered[0]["id"] == 2
        assert filtered[1]["id"] == 3
    
    def test_filter_items_by_keyword(self):
        """Test filtering items by keyword in title."""
        client = HackerNewsAPIClient()
        
        items = [
            {"id": 1, "title": "Python Tutorial", "score": 100},
            {"id": 2, "title": "JavaScript Guide", "score": 100},
            {"id": 3, "title": "Python Best Practices", "score": 100},
        ]
        
        filtered = client.filter_items(items, keyword="Python")
        
        assert len(filtered) == 2
        assert filtered[0]["id"] == 1
        assert filtered[1]["id"] == 3
    
    def test_filter_items_by_keyword_case_insensitive(self):
        """Test filtering items by keyword (case insensitive)."""
        client = HackerNewsAPIClient()
        
        items = [
            {"id": 1, "title": "Python Tutorial", "score": 100},
            {"id": 2, "title": "PYTHON Guide", "score": 100},
            {"id": 3, "title": "python best practices", "score": 100},
        ]
        
        filtered = client.filter_items(items, keyword="python")
        
        assert len(filtered) == 3
    
    def test_filter_items_by_both_criteria(self):
        """Test filtering items by both min_score and keyword."""
        client = HackerNewsAPIClient()
        
        items = [
            {"id": 1, "title": "Python Tutorial", "score": 50},
            {"id": 2, "title": "Python Guide", "score": 100},
            {"id": 3, "title": "JavaScript Tutorial", "score": 100},
            {"id": 4, "title": "Python Best Practices", "score": 150},
        ]
        
        filtered = client.filter_items(items, min_score=100, keyword="Python")
        
        assert len(filtered) == 2
        assert filtered[0]["id"] == 2
        assert filtered[1]["id"] == 4
    
    def test_filter_items_no_criteria(self):
        """Test filtering items with no criteria (should return all items)."""
        client = HackerNewsAPIClient()
        
        items = [
            {"id": 1, "title": "Story 1", "score": 50},
            {"id": 2, "title": "Story 2", "score": 100},
        ]
        
        filtered = client.filter_items(items)
        
        assert len(filtered) == 2
        assert filtered == items
    
    def test_filter_items_empty_list(self):
        """Test filtering empty list of items."""
        client = HackerNewsAPIClient()
        
        filtered = client.filter_items([])
        
        assert len(filtered) == 0
        assert filtered == []
    
    def test_filter_items_missing_score_field(self):
        """Test filtering items with missing score field."""
        client = HackerNewsAPIClient()
        
        items = [
            {"id": 1, "title": "Story 1", "score": 100},
            {"id": 2, "title": "Story 2"},  # Missing score
            {"id": 3, "title": "Story 3", "score": 150},
        ]
        
        filtered = client.filter_items(items, min_score=100)
        
        assert len(filtered) == 2
        assert filtered[0]["id"] == 1
        assert filtered[1]["id"] == 3
    
    def test_filter_items_missing_title_field(self):
        """Test filtering items with missing title field."""
        client = HackerNewsAPIClient()
        
        items = [
            {"id": 1, "title": "Python Story", "score": 100},
            {"id": 2, "score": 100},  # Missing title
            {"id": 3, "title": "Python Guide", "score": 100},
        ]
        
        filtered = client.filter_items(items, keyword="Python")
        
        assert len(filtered) == 2
        assert filtered[0]["id"] == 1
        assert filtered[1]["id"] == 3
