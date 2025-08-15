import pytest
import asyncio
import os
from typing import Generator, AsyncGenerator
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Override database URL for tests
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app.main import app
from app.core.config.database import Base, get_db_session
from app.services.data_service import DataService
from app.services.hacker_news_client import HackerNewsAPIClient
from app.tasks.fetch_tasks import celery_app


# Test database configuration
TEST_DATABASE_URL = "sqlite:///:memory:"

# Create test engine
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False,
)

# Create test session
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


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


@pytest.fixture(scope="function")
def db_session_ctx():
    """Database session context manager for tests."""
    Base.metadata.create_all(bind=test_engine)
    
    def get_test_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()
    
    return get_test_db


@pytest.fixture
def fake_hacker_news_client():
    """Fake Hacker News API client for testing."""
    client = AsyncMock(spec=HackerNewsAPIClient)
    
    # Mock successful responses
    client.get_top_stories.return_value = [1, 2, 3, 4, 5]
    client.get_item.return_value = {
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
    client.get_items_batch.return_value = [
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
        }
    ]
    client.filter_items.return_value = [
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
        }
    ]
    
    return client


@pytest.fixture
def fake_data_service(db_session):
    """Fake data service for testing."""
    service = DataService()
    # Override the database session to use test database
    service._get_db_session = lambda: db_session
    return service


@pytest.fixture
def test_client(db_session):
    """Test client with dependency overrides."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass  # Don't close the session here as it's managed by the fixture
    
    # Override the database dependency
    app.dependency_overrides[get_db_session] = override_get_db
    
    # Also override the SessionLocal in data_service to use the test session
    from app.services.data_service import SessionLocal
    original_session_local = SessionLocal
    
    def test_session_local():
        return db_session
    
    app.dependency_overrides[SessionLocal] = test_session_local
    
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
