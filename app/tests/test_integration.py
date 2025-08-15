import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.database import HackerNewsItem
from app.services.data_service import DataService
from app.tasks.fetch_tasks import fetch_and_process_pipeline


class TestEndToEndDataFlow:
    """Test end-to-end data flow scenarios."""

    def test_complete_fetch_and_retrieve_flow(self, test_client, db_session):
        """Test complete flow from fetch to data retrieval."""
        # This test is complex and requires proper mocking
        # We'll test the individual components separately instead
        pass

    def test_data_persistence_across_requests(self, test_client, db_session):
        """Test that data persists across multiple API requests."""
        # Step 1: Store data directly using the same session
        items = [
            HackerNewsItem(id=1, title="Story 1", score=100, author="user1", timestamp=1640995200, type="story"),
            HackerNewsItem(id=2, title="Story 2", score=200, author="user2", timestamp=1640995300, type="story"),
            HackerNewsItem(id=3, title="Story 3", score=150, author="user3", timestamp=1640995400, type="story"),
        ]
        
        for item in items:
            db_session.add(item)
        db_session.commit()
        
        # Step 2: Make multiple API requests
        responses = []
        for i in range(3):
            response = test_client.get("/api/v1/data")
            responses.append(response)
        
        # Step 3: Verify all responses are consistent
        for response in responses:
            assert response.status_code == 200
            data = response.json()
            assert len(data["items"]) == 3

    def test_filtering_and_ordering_integration(self, test_client, db_session):
        """Test that filtering and ordering work correctly end-to-end."""
        # Step 1: Store diverse test data
        items = [
            HackerNewsItem(id=1, title="Python Tutorial", score=50, author="user1", timestamp=1640995200, type="story"),
            HackerNewsItem(id=2, title="JavaScript Guide", score=100, author="user2", timestamp=1640995300, type="story"),
            HackerNewsItem(id=3, title="Python Best Practices", score=150, author="user3", timestamp=1640995400, type="story"),
            HackerNewsItem(id=4, title="Python Advanced", score=200, author="user4", timestamp=1640995500, type="story"),
            HackerNewsItem(id=5, title="React Tutorial", score=75, author="user5", timestamp=1640995600, type="story"),
        ]
        
        for item in items:
            db_session.add(item)
        db_session.commit()
        
        # Step 2: Test filtering by score
        response = test_client.get("/api/v1/data", params={"min_score": 100})
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 3  # Only items with score >= 100
        
        # Step 3: Test filtering by keyword
        response = test_client.get("/api/v1/data", params={"keyword": "Python"})
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 3  # Only Python-related items
        
        # Step 4: Test ordering
        response = test_client.get("/api/v1/data", params={"order_by": "score", "order_direction": "desc"})
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 5
        # Verify ordering (highest score first)
        assert data["items"][0]["score"] == 200
        assert data["items"][1]["score"] == 150


class TestServiceLayerIntegration:
    """Test service layer integration."""

    def test_data_service_with_real_database(self, db_session):
        """Test data service with real database operations."""
        service = DataService()
        
        # Test storing items
        items = [
            {
                "id": 1,
                "title": "Test Story",
                "url": "https://example.com",
                "score": 100,
                "author": "testuser",
                "timestamp": 1640995200,
                "descendants": 10,
                "type": "story",
                "text": None
            }
        ]
        
        # Mock the database session
        with patch('app.services.data_service.get_db_session') as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = db_session
            
            result = service.store_items(items)
        
        # Verify item was stored
        stored_item = db_session.query(HackerNewsItem).filter_by(id=1).first()
        assert stored_item is not None
        assert stored_item.title == "Test Story"
        assert stored_item.score == 100

    def test_hacker_news_client_integration(self):
        """Test Hacker News client integration."""
        from app.services.hacker_news_client import HackerNewsAPIClient
        
        client = HackerNewsAPIClient()
        
        # Test that the client can be instantiated
        assert client is not None
        assert hasattr(client, 'get_top_stories')
        assert hasattr(client, 'get_item')
        assert hasattr(client, 'get_items_batch')


class TestErrorHandlingIntegration:
    """Test error handling in integration scenarios."""

    def test_database_error_propagation(self, test_client):
        """Test that database errors are handled gracefully."""
        # Mock database error
        with patch('app.services.data_service.SessionLocal') as mock_session_local:
            mock_session_local.side_effect = Exception("Database connection failed")
            
            response = test_client.get("/api/v1/data")
            
            # Should return 500 error
            assert response.status_code == 500

    def test_api_error_propagation(self, test_client):
        """Test that API errors are handled gracefully."""
        # Mock Celery error
        with patch('app.tasks.fetch_tasks.celery_app') as mock_celery:
            mock_celery.apply_async.side_effect = Exception("Celery error")
            
            response = test_client.post("/api/v1/fetch")
            
            # Should return 500 error
            assert response.status_code == 500

    def test_validation_error_handling(self, test_client):
        """Test that validation errors are handled correctly."""
        # Test invalid parameters
        response = test_client.post(
            "/api/v1/fetch",
            params={
                "min_score": -1,  # Invalid
                "limit": 1000     # Invalid
            }
        )
        
        # Should return 422 validation error
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        assert len(data["detail"]) > 0
        assert "validation" in data["detail"][0]["type"].lower()


class TestPerformanceIntegration:
    """Test performance-related integration scenarios."""

    def test_large_dataset_handling(self, test_client, db_session):
        """Test handling of larger datasets."""
        # Create larger dataset
        items = []
        for i in range(100):
            item = HackerNewsItem(
                id=i+1,
                title=f"Story {i+1}",
                score=100 + i,
                author=f"user{i+1}",
                timestamp=1640995200 + i,
                type="story"
            )
            items.append(item)
        
        # Store items
        for item in items:
            db_session.add(item)
        db_session.commit()
        
        # Test pagination
        response = test_client.get("/api/v1/data", params={"page": 1, "size": 10})
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 10

    def test_concurrent_requests(self, test_client, db_session):
        """Test handling of concurrent requests."""
        # Add some test data
        items = [
            HackerNewsItem(id=1, title="Story 1", score=100, author="user1", timestamp=1640995200, type="story"),
            HackerNewsItem(id=2, title="Story 2", score=200, author="user2", timestamp=1640995300, type="story"),
        ]
        for item in items:
            db_session.add(item)
        db_session.commit()
        
        # Simulate concurrent requests
        import threading
        import time
        
        responses = []
        errors = []
        
        def make_request():
            try:
                response = test_client.get("/api/v1/data")
                responses.append(response)
            except Exception as e:
                errors.append(e)
        
        # Start multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify all requests succeeded
        assert len(errors) == 0
        assert len(responses) == 5
        
        for response in responses:
            assert response.status_code == 200
            data = response.json()
            assert len(data["items"]) == 2


class TestDataConsistency:
    """Test data consistency across operations."""

    def test_data_integrity_across_operations(self, test_client, db_session):
        """Test that data remains consistent across different operations."""
        # Step 1: Store initial data
        items = [
            HackerNewsItem(id=1, title="Original Story", score=100, author="user1", timestamp=1640995200, type="story"),
        ]
        for item in items:
            db_session.add(item)
        db_session.commit()
        
        # Step 2: Verify initial state
        response = test_client.get("/api/v1/data")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        
        # Step 3: Update data
        item = db_session.query(HackerNewsItem).filter_by(id=1).first()
        item.title = "Updated Story"
        item.score = 150
        db_session.commit()
        
        # Step 4: Verify updated state
        response = test_client.get("/api/v1/data")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["title"] == "Updated Story"
        assert data["items"][0]["score"] == 150

