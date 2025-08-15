from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import redis.asyncio as redis
from fastapi_pagination import add_pagination

from app.core.config import settings, create_tables, health_check as redis_health_check, setup_logging, get_logger
from app.core.utils import setup_exception_handlers
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter

# Import and include API routes
from app.api.routes import fetch, data

setup_logging()
logger = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting up Hacker News Data Fetcher...")

    # Initialize database tables
    try:
        logger.info("Initializing database tables...")
        create_tables()
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database tables: {e}")
        raise

    # Initialize FastAPI Limiter
    try:
        redis_connection = redis.from_url(settings.redis_url, encoding="utf8", decode_responses=True)
        await FastAPILimiter.init(redis_connection)
        logger.info("FastAPI Limiter initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize FastAPI Limiter: {e}")
        logger.warning("Rate limiting will be disabled")

    yield

    # Shutdown
    try:
        await FastAPILimiter.close()
        logger.info("FastAPI Limiter closed")
    except Exception as e:
        logger.error(f"Error closing FastAPI Limiter: {e}")

    logger.info("Shutting down Hacker News Data Fetcher...")


# Create FastAPI application
app = FastAPI(
    title="Hacker News Data Fetcher",
    description="A FastAPI application for fetching and storing Hacker News data",
    version="1.0.0",
    lifespan=lifespan
)

# Setup global exception handlers
setup_exception_handlers(app)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", dependencies=[Depends(RateLimiter(times=200, seconds=60))])
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Hacker News Data Fetcher API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
    }


@app.get("/health", dependencies=[Depends(RateLimiter(times=100, seconds=60))])
async def health_check():
    """Health check endpoint."""
    health_status = {
        "status": "healthy",
        "database": "connected",
        "redis": "connected" if redis_health_check() else "disconnected",
        "timestamp": "2024-01-01T00:00:00Z",  # TODO: Use actual timestamp
    }

    # Check if any service is unhealthy
    if health_status["redis"] == "disconnected":
        health_status["status"] = "degraded"

    return health_status


@app.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check endpoint for debugging."""
    health_status = {"status": "healthy", "services": {}}

    # Database health check
    try:
        from app.core.config.database import SessionLocal
        from sqlalchemy import text

        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        health_status["services"]["database"] = {"status": "healthy"}
    except Exception as e:
        health_status["services"]["database"] = {"status": "unhealthy", "error": str(e)}
        health_status["status"] = "unhealthy"

    # Redis health check
    if redis_health_check():
        health_status["services"]["redis"] = {"status": "healthy"}
    else:
        health_status["services"]["redis"] = {"status": "unhealthy"}
        health_status["status"] = "unhealthy"

    return health_status


app.include_router(fetch.router, prefix="/api/v1", tags=["fetch"])
app.include_router(data.router, prefix="/api/v1", tags=["data"])

# Add pagination support
add_pagination(app)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True, log_level=settings.log_level.lower())
