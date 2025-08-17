import pytest
import os
from typing import Optional
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.config.database import Base, get_db_session
from app.services.data_service import DataService
from app.tasks.fetch_tasks import celery_app


# Test database configuration
TEST_DATABASE_URL = "sqlite:///:memory:"

# Override database URL for tests
os.environ["DATABASE_URL"] = TEST_DATABASE_URL

# Override Redis URL for tests to use memory mode
os.environ["REDIS_URL"] = "redis://localhost:6379/1"  # Use different DB for tests

# Create test engine
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False,
)

# Create test session
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def disable_rate_limiting():
    """Disable rate limiting for all tests."""
    # Mock the rate limiter to always allow requests
    def mock_rate_limiter(*args, **kwargs):
        def noop_dependency():
            pass
        return noop_dependency
    
    # Mock the get_rate_limit function to return a no-op dependency
    with patch('app.core.config.rate_limit.get_rate_limit', mock_rate_limiter):
        yield


@pytest.fixture(scope="function")
def mock_cache():
    """Mock cache for individual tests."""
    # Create a simple in-memory cache
    cache_storage = {}
    
    class MockCache:
        def get(self, key: str, namespace: str = "default"):
            full_key = f"{namespace}:{key}"
            return cache_storage.get(full_key)
        
        def set(self, key: str, value, ttl: Optional[int] = None, namespace: str = "default"):
            full_key = f"{namespace}:{key}"
            cache_storage[full_key] = value
            return True
        
        def delete(self, key: str, namespace: str = "default"):
            full_key = f"{namespace}:{key}"
            if full_key in cache_storage:
                del cache_storage[full_key]
                return True
            return False
        
        def clear(self):
            cache_storage.clear()
    
    mock_cache_instance = MockCache()
    
    # Mock the global cache instance
    with patch('app.core.config.cache', mock_cache_instance):
        with patch('app.tasks.fetch_tasks.cache', mock_cache_instance):
            yield mock_cache_instance


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test."""
    # Drop and recreate tables to ensure clean state
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    
    # Create session
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def fake_data_service(db_session):
    """Fake data service for testing."""
    service = DataService()
    # Override the database session to use test database
    service._get_db_session = lambda: db_session
    return service


@pytest.fixture
def test_client(db_session, mock_cache):
    """Test client with dependency overrides."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass  # Don't close the session here as it's managed by the fixture
    
    # Override the database dependency
    app.dependency_overrides[get_db_session] = override_get_db
    
    with TestClient(app) as client:
        yield client
    
    app.dependency_overrides.clear()


@pytest.fixture
def celery_test_app():
    """Test Celery app configuration."""
    celery_app.conf.update({
        'task_always_eager': True,  # Execute tasks synchronously
        'task_eager_propagates': True,  # Propagate exceptions
        'broker_url': 'memory://',  # Use in-memory broker
        'result_backend': 'rpc://',  # Use RPC result backend
    })
    return celery_app


@pytest.fixture
def mock_session_local_for_tasks(db_session, monkeypatch):
    """Mock SessionLocal for Celery tasks to use test database session."""
    def mock_session_local():
        return db_session
    
    # Mock SessionLocal in fetch_tasks module
    monkeypatch.setattr("app.tasks.fetch_tasks.SessionLocal", mock_session_local)
    return db_session


@pytest.fixture
def sample_hacker_news_items():
    """Sample Hacker News items for testing."""
    return [
        {
            "id": 1,
            "title": "Test Story 1",
            "url": "https://example.com/1",
            "score": 100,
            "author": "testuser1",
            "timestamp": 1640995200,
            "descendants": 10,
            "type": "story",
            "text": None
        },
        {
            "id": 2,
            "title": "Test Story 2",
            "url": "https://example.com/2",
            "score": 200,
            "author": "testuser2",
            "timestamp": 1640995300,
            "descendants": 20,
            "type": "story",
            "text": None
        },
        {
            "id": 3,
            "title": "AI News Story",
            "url": "https://example.com/3",
            "score": 150,
            "author": "testuser3",
            "timestamp": 1640995400,
            "descendants": 15,
            "type": "story",
            "text": None
        }
    ]



