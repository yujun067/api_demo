from datetime import datetime, timezone
from fastapi import APIRouter, Query, Depends

from app.models.api import FetchRequest, FetchResponse

from app.tasks.fetch_tasks import fetch_and_process_pipeline, get_task_status
from app.core.utils import NotFoundException
from app.core.config.logging import get_logger
from app.core.config import get_rate_limit

logger = get_logger("fetch")

router = APIRouter()


@router.post(
    "/fetch",
    response_model=FetchResponse,
    summary="Trigger data fetching job",
    description="Fetch Hacker News data with optional filtering and store in database",
    dependencies=[Depends(get_rate_limit("fetch"))],
    status_code=202,
)
async def fetch_data(request: FetchRequest = Query(...)):
    """
    Trigger a job to fetch data from Hacker News API.

    Query Parameters:
    - **min_score**: Filter items by minimum score
    - **keyword**: Filter items by keyword in title
    - **limit**: Number of items to fetch (max 500)

    Returns a task ID for tracking the fetch operation.
    """
    logger.info(f"Starting fetch task with params: {request.model_dump()}")

    # Start Celery task
    task = fetch_and_process_pipeline.apply_async(args=[request.min_score, request.keyword, request.limit])

    logger.info(f"Fetch task {task.id} accepted and queued")
    return FetchResponse(
        task_id=task.id, status="accepted", message="Data fetching job started", timestamp=datetime.now(timezone.utc)
    )


@router.get(
    "/fetch/{task_id}",
    summary="Get task status",
    description="Get the status of a fetch task by task ID",
    dependencies=[Depends(get_rate_limit("task_status"))],
)
async def get_task_status_endpoint(task_id: str):
    """
    Get the status of a fetch task.

    - **task_id**: The task ID returned from the fetch endpoint
    """
    task_status = get_task_status(task_id)

    if not task_status:
        raise NotFoundException(resource="Task", resource_id=task_id)

    return task_status
