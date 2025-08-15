import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.services.data_service import data_service
from app.services.hacker_news_client import hacker_news_client
from app.tasks.fetch_tasks import celery_app
from app.models.database import HackerNewsItem


class TestFetchAPI:
    """Test fetch API endpoints with mocked external dependencies."""
    
    def test_fetch_data_success(self, test_client, fake_hacker_news_client, celery_test_app):
        """Test successful fetch data request."""
        # Mock Celery task
        mock_task = MagicMock()
        mock_task.id = "test-task-123"
        
        with patch.object(celery_app, 'apply_async') as mock_apply_async:
            mock_apply_async.return_value = mock_task
            
            response = test_client.post(
                "/api/v1/fetch",
                params={
                    "min_score": 100,
                    "keyword": "Python",
                    "limit": 50
                }
            )
        
        assert response.status_code == 202
        data = response.json()
        assert data["task_id"] == "test-task-123"
        assert data["status"] == "accepted"
        assert data["message"] == "Data fetching job started"
        assert "timestamp" in data
        
        # Verify Celery task was called with correct parameters
        mock_apply_async.assert_called_once_with(args=[100, "Python", 50])
    
    def test_fetch_data_default_parameters(self, test_client, celery_test_app):
        """Test fetch data request with default parameters."""
        mock_task = MagicMock()
        mock_task.id = "test-task-default"
        
        with patch.object(celery_app, 'apply_async') as mock_apply_async:
            mock_apply_async.return_value = mock_task
            
            response = test_client.post("/api/v1/fetch")
        
        assert response.status_code == 202
        data = response.json()
        assert data["task_id"] == "test-task-default"
        assert data["status"] == "accepted"
        
        # Verify default parameters were used
        mock_apply_async.assert_called_once_with(args=[None, None, 100])
    
    def test_fetch_data_invalid_parameters(self, test_client):
        """Test fetch data request with invalid parameters."""
        response = test_client.post(
            "/api/v1/fetch",
            params={
                "min_score": -1,  # Invalid: negative score
                "limit": 1000     # Invalid: exceeds maximum
            }
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_get_task_status_success(self, test_client):
        """Test getting task status successfully."""
        # Mock task status in cache
        mock_task_status = {
            "task_id": "test-task-123",
            "status": "processing",
            "progress": 50,
            "message": "Fetching item details",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:01:00Z"
        }
        
        with patch('app.tasks.fetch_tasks.get_task_status') as mock_get_status:
            mock_get_status.return_value = mock_task_status
            
            response = test_client.get("/api/v1/fetch/test-task-123")
        
        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == "test-task-123"
        assert data["status"] == "processing"
        assert data["progress"] == 50
        assert data["message"] == "Fetching item details"
    
    def test_get_task_status_not_found(self, test_client):
        """Test getting status for non-existent task."""
        with patch('app.tasks.fetch_tasks.get_task_status') as mock_get_status:
            mock_get_status.return_value = None
            
            response = test_client.get("/api/v1/fetch/non-existent-task")
        
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()
        assert "Task" in data["detail"]
        assert "non-existent-task" in data["detail"]


class TestDataAPI:
    """Test data API endpoints with mocked services."""
    
    def test_get_data_basic(self, test_client, db_session):
        """Test basic data retrieval without filters."""
        # Add test data to database
        items = [
            HackerNewsItem(id=1, title="Story 1", score=100, author="user1", timestamp=1640995200, type="story"),
            HackerNewsItem(id=2, title="Story 2", score=200, author="user2", timestamp=1640995300, type="story"),
        ]
        for item in items:
            db_session.add(item)
        db_session.commit()
        
        response = test_client.get("/api/v1/data")
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "size" in data
        assert "pages" in data
        
        # Verify items are returned (ordered by score desc by default)
        items_data = data["items"]
        assert len(items_data) == 2
        assert items_data[0]["id"] == 2  # Higher score first
        assert items_data[1]["id"] == 1
    
    def test_get_data_with_filters(self, test_client, db_session):
        """Test data retrieval with filters."""
        # Add test data
        items = [
            HackerNewsItem(id=1, title="Python Tutorial", score=50, author="user1", timestamp=1640995200, type="story"),
            HackerNewsItem(id=2, title="JavaScript Guide", score=100, author="user2", timestamp=1640995300, type="story"),
            HackerNewsItem(id=3, title="Python Best Practices", score=150, author="user3", timestamp=1640995400, type="story"),
        ]
        for item in items:
            db_session.add(item)
        db_session.commit()
        
        response = test_client.get(
            "/api/v1/data",
            params={
                "min_score": 100,
                "keyword": "Python",
                "order_by": "score",
                "order_direction": "desc"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        items_data = data["items"]
        
        # Should only return Python stories with score >= 100
        assert len(items_data) == 1
        assert items_data[0]["id"] == 3
        assert items_data[0]["title"] == "Python Best Practices"
        assert items_data[0]["score"] == 150
    
    def test_get_data_by_id(self, test_client, db_session):
        """Test getting specific item by ID."""
        # Add test item
        item = HackerNewsItem(id=12345, title="Specific Story", score=100, author="user1", timestamp=1640995200, type="story")
        db_session.add(item)
        db_session.commit()
        
        response = test_client.get("/api/v1/data", params={"item_id": 12345})
        
        assert response.status_code == 200
        data = response.json()
        items_data = data["items"]
        
        assert len(items_data) == 1
        assert items_data[0]["id"] == 12345
        assert items_data[0]["title"] == "Specific Story"
    
    def test_get_data_by_id_not_found(self, test_client):
        """Test getting item by ID that doesn't exist."""
        response = test_client.get("/api/v1/data", params={"item_id": 99999})
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 0
        assert data["total"] == 0
    
    def test_get_data_pagination(self, test_client, db_session):
        """Test data retrieval with pagination."""
        # Add test data
        items = []
        for i in range(15):
            item = HackerNewsItem(
                id=i+1,
                title=f"Story {i+1}",
                score=100 + i,
                author=f"user{i+1}",
                timestamp=1640995200 + i,
                type="story"
            )
            items.append(item)
        
        for item in items:
            db_session.add(item)
        db_session.commit()
        
        # Test first page
        response = test_client.get("/api/v1/data", params={"page": 1, "size": 5})
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 5
        assert data["page"] == 1
        assert data["size"] == 5
        assert data["total"] == 15
        assert data["pages"] == 3
        
        # Test second page
        response = test_client.get("/api/v1/data", params={"page": 2, "size": 5})
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 5
        assert data["page"] == 2
    
    def test_get_data_invalid_parameters(self, test_client):
        """Test data retrieval with invalid parameters."""
        # Test invalid order_by
        response = test_client.get("/api/v1/data", params={"order_by": "invalid"})
        assert response.status_code == 422
        
        # Test invalid order_direction
        response = test_client.get("/api/v1/data", params={"order_direction": "invalid"})
        assert response.status_code == 422
        
        # Test negative min_score
        response = test_client.get("/api/v1/data", params={"min_score": -1})
        assert response.status_code == 422
    
    def test_get_data_empty_database(self, test_client):
        """Test data retrieval from empty database."""
        response = test_client.get("/api/v1/data")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 0
        assert data["total"] == 0
        assert data["page"] == 1
        assert data["size"] == 10


class TestHealthCheckAPI:
    """Test health check endpoints."""
    
    def test_root_endpoint(self, test_client):
        """Test root endpoint."""
        response = test_client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Hacker News Data Fetcher API"
        assert data["version"] == "1.0.0"
        assert data["docs"] == "/docs"
        assert data["redoc"] == "/redoc"
    
    def test_health_check(self, test_client):
        """Test basic health check endpoint."""
        with patch('app.core.config.redis_health_check') as mock_redis_health:
            mock_redis_health.return_value = True
            
            response = test_client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["database"] == "connected"
        assert data["redis"] == "connected"
        assert "timestamp" in data
    
    def test_health_check_redis_disconnected(self, test_client):
        """Test health check when Redis is disconnected."""
        with patch('app.core.config.redis_health_check') as mock_redis_health:
            mock_redis_health.return_value = False
            
            response = test_client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "degraded"
        assert data["redis"] == "disconnected"
    
    def test_detailed_health_check_success(self, test_client, db_session):
        """Test detailed health check endpoint."""
        with patch('app.core.config.redis_health_check') as mock_redis_health:
            mock_redis_health.return_value = True
            
            response = test_client.get("/health/detailed")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "services" in data
        assert data["services"]["database"]["status"] == "healthy"
        assert data["services"]["redis"]["status"] == "healthy"
    
    def test_detailed_health_check_database_error(self, test_client):
        """Test detailed health check when database is unhealthy."""
        # Mock database error by making SessionLocal raise an exception
        with patch('app.core.config.database.SessionLocal') as mock_session_local:
            mock_session_local.side_effect = Exception("Database connection failed")
            
            with patch('app.core.config.redis_health_check') as mock_redis_health:
                mock_redis_health.return_value = True
                
                response = test_client.get("/health/detailed")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "unhealthy"
        assert data["services"]["database"]["status"] == "unhealthy"
        assert "error" in data["services"]["database"]


class TestRateLimiting:
    """Test rate limiting functionality."""
    
    def test_rate_limiting_fetch_endpoint(self, test_client):
        """Test rate limiting on fetch endpoint."""
        # Mock Celery task
        mock_task = MagicMock()
        mock_task.id = "test-task"
        
        with patch.object(celery_app, 'apply_async') as mock_apply_async:
            mock_apply_async.return_value = mock_task
            
            # Make multiple requests to trigger rate limiting
            responses = []
            for i in range(10):  # Should be well within limit
                response = test_client.post("/api/v1/fetch")
                responses.append(response)
        
        # All requests should succeed
        for response in responses:
            assert response.status_code == 202
    
    def test_rate_limiting_data_endpoint(self, test_client):
        """Test rate limiting on data endpoint."""
        # Make multiple requests to trigger rate limiting
        responses = []
        for i in range(10):  # Should be well within limit
            response = test_client.get("/api/v1/data")
            responses.append(response)
        
        # All requests should succeed
        for response in responses:
            assert response.status_code == 200


class TestErrorHandling:
    """Test error handling in API endpoints."""
    
    def test_invalid_json_request(self, test_client):
        """Test handling of invalid JSON in request body."""
        response = test_client.post(
            "/api/v1/fetch",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422
    
    def test_missing_required_parameters(self, test_client):
        """Test handling of missing required parameters."""
        # This should work as all parameters are optional
        response = test_client.post("/api/v1/fetch")
        assert response.status_code == 202
    
    def test_database_connection_error(self, test_client):
        """Test handling of database connection errors."""
        # Mock database error
        with patch('app.services.data_service.SessionLocal') as mock_session_local:
            mock_session_local.side_effect = Exception("Database connection failed")
            
            response = test_client.get("/api/v1/data")
        
        # Should handle the error gracefully
        assert response.status_code == 500
    
    def test_celery_task_error(self, test_client):
        """Test handling of Celery task errors."""
        with patch.object(celery_app, 'apply_async') as mock_apply_async:
            mock_apply_async.side_effect = Exception("Celery error")
            
            response = test_client.post("/api/v1/fetch")
        
        # Should handle the error gracefully
        assert response.status_code == 500
