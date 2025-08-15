# Hacker News Data Fetcher

A robust, scalable backend service for fetching, processing, and serving Hacker News data with advanced filtering, caching, and real-time processing capabilities. Built with FastAPI, Celery, Redis, and SQLite for simplicity and performance.

## 🚀 Features

- **Real-time Data Fetching**: Asynchronous fetching from Hacker News API
- **Advanced Filtering**: Filter by score, keywords, and custom criteria
- **RESTful API**: Clean, documented API endpoints with OpenAPI/Swagger
- **Database Storage**: Persistent storage with SQLAlchemy ORM
- **Caching Layer**: Redis-based caching for improved performance
- **Rate Limiting**: Built-in rate limiting to prevent API abuse
- **Background Processing**: Celery-based task queue for async operations
- **Health Monitoring**: Comprehensive health checks and monitoring
- **Docker Support**: Containerized deployment with Docker Compose
- **Testing**: Comprehensive test suite with pytest

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI App   │    │   Celery Worker │    │   Redis Cache   │
│   (Port 8000)   │◄──►│   (Background)  │◄──►│   (Port 6379)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   SQLite DB     │    │  Hacker News    │    │   Rate Limiting │
│   (File-based)  │    │     API         │    │   & Caching     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Project Structure
```
backend_demo/
├── app/                          # Main application package
│   ├── __init__.py
│   ├── main.py                   # FastAPI application entry point
│   ├── api/                      # API layer
│   │   ├── __init__.py
│   │   └── routes/               # API route definitions
│   │       ├── __init__.py
│   │       ├── data.py           # Data retrieval endpoints
│   │       └── fetch.py          # Data fetching endpoints
│   ├── core/                     # Core application components
│   │   ├── __init__.py
│   │   ├── config/               # Configuration management
│   │   │   ├── __init__.py
│   │   │   ├── database.py       # Database configuration
│   │   │   ├── logging.py        # Logging configuration
│   │   │   ├── rate_limit.py     # Rate limiting configuration
│   │   │   ├── redis.py          # Redis configuration
│   │   │   └── settings.py       # Application settings
│   │   └── utils/                # Utility functions
│   │       ├── __init__.py
│   │       └── exceptions.py     # Custom exceptions
│   ├── models/                   # Data models
│   │   ├── __init__.py
│   │   ├── common.py             # Common model utilities
│   │   ├── database.py           # SQLAlchemy ORM models
│   │   └── schemas.py            # Pydantic schemas
│   ├── services/                 # Business logic layer
│   │   ├── __init__.py
│   │   ├── data_service.py       # Data management service
│   │   └── hacker_news_client.py # Hacker News API client
│   ├── tasks/                    # Background task processing
│   │   ├── __init__.py
│   │   ├── celery_app.py         # Celery application configuration
│   │   └── fetch_tasks.py        # Data fetching tasks
│   └── tests/                    # Comprehensive test suite
│       ├── __init__.py
│       ├── conftest.py           # Test configuration and fixtures
│       ├── test_domain_logic.py  # Pure domain logic tests
│       ├── test_services.py      # Service layer tests
│       ├── test_repositories.py  # Repository tests
│       ├── test_api.py           # API endpoint tests
│       ├── test_tasks.py         # Task processing tests
│       └── test_integration.py   # End-to-end integration tests
├── data/                         # Data storage
│   └── hacker_news.db            # SQLite database file
├── .venv/                        # Python virtual environment
├── .gitignore                    # Git ignore rules
├── .coverage                     # Test coverage data
├── docker-compose.yml            # Docker services configuration
├── Dockerfile                    # Application container definition
├── env.example                   # Environment variables template
├── requirements.txt              # Python dependencies
├── run_tests.sh                  # Test runner script
└── README.md                     # Project documentation
```

## 📋 Prerequisites

- Python 3.12+
- Docker & Docker Compose
- Redis (for caching and task queue)
- SQLite (built-in, no additional setup required)

## 🛠️ Installation & Setup

### Option 1: Docker Deployment (Recommended)

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd backend_demo
   ```

2. **Set up environment variables (optional)**
   ```bash
   cp env.example .env
   # Edit .env with your configuration if needed
   ```

3. **Start with Docker Compose**
   ```bash
   docker-compose up -d
   ```

4. **Verify deployment**
   ```bash
   docker-compose ps
   curl http://localhost:8000/health
   ```

### Option 2: Local Development

1. **Create virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   cp env.example .env
   # Configure your .env file
   ```

4. **Run the application**
   ```bash
   # Start Redis (using Docker)
   docker-compose up -d redis
   
   # Start the application
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   
   # Start Celery worker (in another terminal)
   celery -A app.tasks.celery_app worker --loglevel=info
   ```

## 🚀 Quick Start

### Docker Deployment
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild and start
docker-compose up --build -d
```

### Local Development
```bash
# Start only Redis for local development
docker-compose up -d redis

# Run the application locally
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Start Celery worker (in another terminal)
celery -A app.tasks.celery_app worker --loglevel=info
```

### Verify Installation
1. **Check health status**
   ```bash
   curl http://localhost:8000/health
   ```

2. **Fetch Hacker News data**
   ```bash
   curl -X POST http://localhost:8000/api/v1/fetch \
     -H "Content-Type: application/json" \
     -d '{"min_score": 100, "keyword": "AI", "limit": 10}'
   ```

3. **Retrieve stored data**
   ```bash
   curl http://localhost:8000/api/v1/data
   ```

4. **Access API documentation**
   ```
   http://localhost:8000/docs
   ```

## 📚 API Documentation

### Base URL
```
http://localhost:8000/api/v1
```

### Endpoints

#### Health Check
- `GET /health` - Basic health status
- `GET /health/detailed` - Detailed health information

#### Data Fetching
- `POST /fetch` - Trigger data fetching job, return task_id
  - Query Parameters:
    - `min_score` (optional): Minimum score filter
    - `keyword` (optional): Keyword filter in title
    - `limit` (optional): Number of items to fetch (max 500)

- `GET /fetch/{task_id}` - Get task status by task_id

#### Data Retrieval
- `GET /data` - Retrieve stored data
  - Query Parameters:
    - `page` (optional): Page number (default: 1)
    - `items_per_page` (optional): Items per page (default: 20)
    - `min_score` (optional): Filter by minimum score
    - `keyword` (optional): Filter by keyword

### Example API Usage

```bash
# Fetch high-scoring AI articles
curl -X POST "http://localhost:8000/api/v1/fetch?min_score=100&keyword=AI&limit=20"

# Get paginated data
curl "http://localhost:8000/api/v1/data?page=1&items_per_page=10"


```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | SQLite database path | `sqlite:////data/hacker_news.db` |
| `REDIS_URL` | Redis connection string | `redis://redis:6379/0` |
| `CELERY_BROKER_URL` | Celery broker URL | `redis://redis:6379/0` |
| `CELERY_RESULT_BACKEND` | Celery result backend | `redis://redis:6379/0` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `APP_ENV` | Environment (dev/prod) | `dev` |

### Rate Limiting

The API includes built-in rate limiting:
- Fetch endpoint: 10 requests per minute
- Data endpoints: 60 requests per minute
- Task status endpoint: 30 requests per minute
- Health endpoint: 100 requests per minute
- Root endpoint: 200 requests per minute

## 🧪 Testing

### Testing Strategy
This project follows a comprehensive testing strategy that focuses on **observable behavior** rather than implementation details:

- **Domain Logic Tests**: Pure, mock-free tests for business rules
- **Service Layer Tests**: Use fakes for repositories, mock external systems
- **Repository Tests**: Connect to lightweight real dependencies (SQLite in-memory)
- **API Tests**: Run through FastAPI's TestClient with fake services
- **Task Tests**: Mock external systems while testing task logic
- **Integration Tests**: End-to-end tests with real components

### Run Tests
```bash
# Run all tests (recommended)
./run_tests.sh

# Run specific test categories
pytest app/tests/test_domain_logic.py -v    # Domain logic tests
pytest app/tests/test_services.py -v        # Service layer tests
pytest app/tests/test_repositories.py -v    # Repository tests
pytest app/tests/test_api.py -v             # API tests
pytest app/tests/test_tasks.py -v           # Task tests
pytest app/tests/test_integration.py -v     # Integration tests
```


## 📊 Monitoring & Logging

### Health Checks
- Application health: `GET /health`
- Detailed health: `GET /health/detailed`
- Database connectivity
- Redis connectivity
- Celery worker status

### Task Monitoring
This project uses **Flower** for comprehensive Celery task monitoring and management through the `hn-flower` container.

#### Access Flower Dashboard
- **Web Dashboard**: http://localhost:5555/
- **Container Name**: `hn-flower`

#### Flower Features
- **Real-time monitoring** of Celery workers and tasks
- **Task management** (revoke, terminate, retry)
- **Worker control** (restart, scale, shutdown)
- **Performance metrics** and statistics
- **RESTful API** for integration
- **WebSocket** for real-time updates

#### API Task Monitoring
You can also monitor tasks through the API endpoints:

```bash
# Get task status
curl http://localhost:8000/api/v1/fetch/{task_id}

# Check task progress and results
```

### Task Management
- **Background Processing**: Asynchronous data fetching and processing
- **Task Status Tracking**: Real-time task status updates
- **Error Handling**: Comprehensive error handling and retry logic
- **Task Scheduling**: Configurable task scheduling for periodic data fetching

### Logging
- Structured logging with different levels
- Request/response logging
- Error tracking and monitoring
- Performance metrics

## 🐳 Docker Deployment

### Services

#### Essential Services (Always Running)
- **web**: FastAPI application (Port 8000)
- **redis**: Redis cache and message broker (Port 6379)
- **worker**: Celery background worker
- **scheduler**: Celery beat scheduler

#### Optional Services (Use Profiles)
- **test**: Test runner (Profile: `test`)

### Deployment Options

#### Standard Setup (Recommended)
```bash
# Start all essential services
docker-compose up -d

# This starts: web + redis + worker + scheduler
```

#### Run Tests
```bash
# Run tests in containerized environment
docker-compose --profile test up test
```

### Commands
```bash
# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild and restart
docker-compose up -d --build

# Scale workers
docker-compose up -d --scale worker=3
```

## 🔍 Troubleshooting

### Common Issues

1. **Redis Connection Failed**
   - Check if Redis is running: `docker-compose ps redis`
   - Verify Redis URL in settings

2. **Database Connection Failed**
   - Ensure SQLite database directory exists: `mkdir -p data`
   - Check database path in `.env`

3. **Celery Tasks Not Processing**
   - Verify Celery worker is running
   - Check Redis connection for message broker

4. **Rate Limiting Issues**
   - Check Redis connectivity
   - Verify rate limiting configuration

5. **Test Failures**
   - Ensure virtual environment is activated: `source .venv/bin/activate`
   - Check that all dependencies are installed: `pip install -r requirements.txt`
   - Verify test database configuration in `conftest.py`

### Debug Mode
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
docker-compose up -d
```

## Performance

- **Caching**: Redis-based caching for frequently accessed data
- **Pagination**: Efficient pagination for large datasets using fastapi-pagination
- **Async Processing**: Non-blocking API operations with Celery background tasks
- **Database Optimization**: SQLite with indexed queries and optimized ORM operations
- **Rate Limiting**: Built-in rate limiting to prevent API abuse
- **Background Processing**: Asynchronous data fetching and processing



## Support

For support and questions:
- Check the API documentation at `/docs`
- Review the troubleshooting section

