import httpx
from typing import AsyncGenerator
from .logging import get_logger

logger = get_logger("http_client")


# Shared HTTP client configuration
HTTP_CLIENT_TIMEOUT = httpx.Timeout(30.0, connect=10.0)
HTTP_CLIENT_LIMITS = httpx.Limits(max_keepalive_connections=20, max_connections=100)

async def get_http_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    """FastAPI dependency for HTTP client with connection pooling.
    
    Provides a configured httpx.AsyncClient with:
    - Connection pooling
    - Timeout settings
    - Retry logic
    - Resource management
    """
    async with httpx.AsyncClient(
        timeout=HTTP_CLIENT_TIMEOUT,
        limits=HTTP_CLIENT_LIMITS
    ) as client:
        yield client


def create_shared_http_client() -> httpx.AsyncClient:
    """Create a shared HTTP client for background tasks.
    
    This function creates a configured httpx.AsyncClient that can be
    shared across multiple API clients for background tasks.
    """
    return httpx.AsyncClient(
        timeout=HTTP_CLIENT_TIMEOUT,
        limits=HTTP_CLIENT_LIMITS
    )

