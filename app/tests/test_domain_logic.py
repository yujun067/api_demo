import pytest
from app.models.api import DataQueryParams
from app.services.hacker_news_client import HackerNewsAPIClient


class TestDataQueryParamsCustomValidation:
    """Test only the custom validation logic in DataQueryParams."""
    
    def test_keyword_validation_empty_string(self):
        """Test custom keyword validation for empty string."""
        params = DataQueryParams(keyword="   ")
        assert params.keyword is None
    
    def test_keyword_validation_whitespace_only(self):
        """Test custom keyword validation for whitespace-only string."""
        params = DataQueryParams(keyword="  \t\n  ")
        assert params.keyword is None
    
    def test_keyword_validation_normal_string(self):
        """Test custom keyword validation for normal string."""
        params = DataQueryParams(keyword="python")
        assert params.keyword == "python"
    
    def test_order_by_validation_invalid_value(self):
        """Test custom order_by validation."""
        with pytest.raises(ValueError, match="order_by must be one of"):
            DataQueryParams(order_by="invalid")
    
    def test_order_by_validation_valid_values(self):
        """Test custom order_by validation with valid values."""
        valid_values = ["score", "time", "id"]
        for value in valid_values:
            params = DataQueryParams(order_by=value)
            assert params.order_by == value
    
    def test_order_direction_validation_invalid_value(self):
        """Test custom order_direction validation."""
        with pytest.raises(ValueError, match="order_direction must be one of"):
            DataQueryParams(order_direction="invalid")
    
    def test_order_direction_validation_valid_values(self):
        """Test custom order_direction validation with valid values."""
        valid_values = ["asc", "desc"]
        for value in valid_values:
            params = DataQueryParams(order_direction=value)
            assert params.order_direction == value


class TestHackerNewsClientBusinessLogic:
    """Test business logic in HackerNewsAPIClient."""
    
    def test_transform_item_fields(self):
        """Test custom field transformation logic."""
        client = HackerNewsAPIClient()
        
        # Test "by" -> "author" transformation
        item = {"id": 1, "by": "testuser", "time": 1640995200}
        transformed = client.transform_item_fields(item)
        
        assert "author" in transformed
        assert "by" not in transformed
        assert transformed["author"] == "testuser"
        
        # Test "time" -> "timestamp" transformation
        assert "timestamp" in transformed
        assert "time" not in transformed
        assert transformed["timestamp"] == 1640995200
    
    def test_filter_items_complex_logic(self):
        """Test complex filtering logic with multiple criteria."""
        client = HackerNewsAPIClient()
        
        items = [
            {"id": 1, "title": "Python Tutorial", "score": 50, "by": "user1", "time": 1640995200},
            {"id": 2, "title": "Python Guide", "score": 100, "by": "user2", "time": 1640995300},
            {"id": 3, "title": "JavaScript Tutorial", "score": 100, "by": "user3", "time": 1640995400},
            {"id": 4, "title": "Python Best Practices", "score": 150, "by": "user4", "time": 1640995500},
        ]
        
        # Test filtering by both score and keyword
        filtered = client.filter_items(items, min_score=100, keyword="Python")
        
        assert len(filtered) == 2
        assert filtered[0]["id"] == 2
        assert filtered[1]["id"] == 4
        
        # Verify field transformation happened
        assert "author" in filtered[0]
        assert "timestamp" in filtered[0]
        assert "by" not in filtered[0]
        assert "time" not in filtered[0]
    
    def test_filter_items_edge_cases(self):
        """Test filtering logic edge cases."""
        client = HackerNewsAPIClient()
        
        # Test with missing fields
        items = [
            {"id": 1, "title": "Python Story", "score": 100},
            {"id": 2, "score": 100},  # Missing title
            {"id": 3, "title": "Python Guide"},  # Missing score
        ]
        
        # Should handle missing fields gracefully
        filtered = client.filter_items(items, min_score=100, keyword="Python")
        assert len(filtered) == 1
        assert filtered[0]["id"] == 1
    
    def test_filter_items_case_insensitive(self):
        """Test case-insensitive keyword filtering."""
        client = HackerNewsAPIClient()
        
        items = [
            {"id": 1, "title": "Python Tutorial", "score": 100},
            {"id": 2, "title": "PYTHON Guide", "score": 100},
            {"id": 3, "title": "python best practices", "score": 100},
        ]
        
        filtered = client.filter_items(items, keyword="python")
        assert len(filtered) == 3
    
    def test_filter_items_empty_input(self):
        """Test filtering with empty input."""
        client = HackerNewsAPIClient()
        
        filtered = client.filter_items([])
        assert filtered == []
        
        filtered = client.filter_items([], min_score=100, keyword="python")
        assert filtered == []


class TestDomainLogicIntegration:
    """Test integration between domain models and business logic."""
    
    def test_query_params_with_filtering_integration(self):
        """Test that query params work correctly with filtering logic."""
        # Create query params with custom validation
        params = DataQueryParams(
            min_score=100,
            keyword="python",  # Use clean keyword
            order_by="score",
            order_direction="desc"
        )
        
        # Use these params with filtering logic
        client = HackerNewsAPIClient()
        items = [
            {"id": 1, "title": "Python Tutorial", "score": 50, "by": "user1", "time": 1640995200},
            {"id": 2, "title": "Python Guide", "score": 100, "by": "user2", "time": 1640995300},
            {"id": 3, "title": "JavaScript Guide", "score": 100, "by": "user3", "time": 1640995400},
        ]
        
        # Apply the same filtering logic
        filtered = client.filter_items(
            items, 
            min_score=params.min_score, 
            keyword=params.keyword
        )
        
        assert len(filtered) == 1
        assert filtered[0]["id"] == 2
        assert filtered[0]["title"] == "Python Guide"
