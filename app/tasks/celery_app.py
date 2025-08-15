from celery import Celery  # type: ignore
from app.core.config import settings

# Create Celery app
celery_app = Celery(
    "hacker_news_tasks",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.tasks.fetch_tasks"],
)

# Celery configuration
celery_app.conf.update(
    # Task serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Task routing
    task_routes={
        "app.tasks.fetch_tasks.*": {"queue": "fetch_queue"},
    },
    # Task execution
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_always_eager=False,  # Set to True for testing without workers
    # Result backend
    result_expires=3600,  # 1 hour
    # Beat schedule for periodic tasks
    beat_schedule={
        "fetch-hacker-news-periodic": {
            "task": "app.tasks.fetch_tasks.scheduled_fetch_task",
            "schedule": settings.fetch_interval_minutes * 60,  # Convert minutes to seconds
            "args": (),
            "kwargs": {"min_score": 50, "limit": 100},
        },
    },
    # Worker configuration
    worker_max_tasks_per_child=1000,
    worker_disable_rate_limits=False,
    # Logging
    worker_log_format="[%(asctime)s: %(levelname)s/%(processName)s] %(message)s",
    worker_task_log_format="[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s",
)

# Optional: Configure task-specific settings
celery_app.conf.task_routes = {
    "app.tasks.fetch_tasks.fetch_top_stories": {"queue": "fetch_queue"},
    "app.tasks.fetch_tasks.fetch_item_details": {"queue": "fetch_queue"},
    "app.tasks.fetch_tasks.process_and_store_items": {"queue": "process_queue"},
    "app.tasks.fetch_tasks.scheduled_fetch_task": {"queue": "scheduler_queue"},
}

if __name__ == "__main__":
    celery_app.start()
