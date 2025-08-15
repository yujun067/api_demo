import asyncio
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

from app.tasks.celery_app import celery_app
from app.services.hacker_news_client import hacker_news_client
from app.services.data_service import data_service
from app.core.config import cache, get_logger

logger = get_logger("celery_tasks")


@celery_app.task(bind=True, name="app.tasks.fetch_tasks.fetch_top_stories")
def fetch_top_stories(self, limit: int = 100) -> List[int]:
    """
    Fetch top stories IDs from Hacker News API.

    Args:
        limit: Number of stories to fetch (default: 100)

    Returns:
        List of story IDs
    """
    task_id = self.request.id
    logger.info(f"Starting fetch_top_stories task {task_id} with limit={limit}")

    try:
        # Run async function in sync context
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(asyncio.run, hacker_news_client.get_top_stories(limit=limit))
            story_ids = future.result()

        logger.info(f"Task {task_id} completed: fetched {len(story_ids)} story IDs")

        return story_ids

    except Exception as e:
        error_msg = f"Failed to fetch top stories: {str(e)}"
        logger.error(f"Task {task_id} failed: {error_msg}")
        update_task_status(task_id, "failed", 0, error_msg)
        raise


@celery_app.task(bind=True, name="app.tasks.fetch_tasks.fetch_item_details")
def fetch_item_details(self, item_ids: List[int]) -> List[Dict[str, Any]]:
    """
    Fetch detailed information for multiple items.

    Args:
        item_ids: List of item IDs to fetch

    Returns:
        List of item details
    """
    task_id = self.request.id
    logger.info(f"Starting fetch_item_details task {task_id} for {len(item_ids)} items")

    try:
        # Run async function in sync context
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(asyncio.run, hacker_news_client.get_items_batch(item_ids))
            items = future.result()

        logger.info(f"Task {task_id} completed: fetched {len(items)} item details")

        return items

    except Exception as e:
        error_msg = f"Failed to fetch item details: {str(e)}"
        logger.error(f"Task {task_id} failed: {error_msg}")
        update_task_status(task_id, "failed", 0, error_msg)
        raise


@celery_app.task(bind=True, name="app.tasks.fetch_tasks.process_and_store_items")
def process_and_store_items(
    self, items: List[Dict[str, Any]], min_score: Optional[int] = None, keyword: Optional[str] = None
) -> Dict[str, Any]:
    """
    Process and store items in the database.

    Args:
        items: List of items to process
        min_score: Minimum score filter
        keyword: Keyword filter

    Returns:
        Processing results
    """
    task_id = self.request.id
    logger.info(f"Starting process_and_store_items task {task_id} for {len(items)} items")

    try:
        # Apply filters
        filtered_items = hacker_news_client.filter_items(items, min_score=min_score, keyword=keyword)

        # Store in database
        stored_item = data_service.store_items(filtered_items)

        result = {
            "items_processed": len(items),
            "items_filtered": len(filtered_items),
            "items_stored": len(filtered_items) if stored_item else 0,
            "filters_applied": {"min_score": min_score, "keyword": keyword},
        }

        logger.info(f"Task {task_id} completed: {result}")
        return result

    except Exception as e:
        error_msg = f"Failed to process and store items: {str(e)}"
        logger.error(f"Task {task_id} failed: {error_msg}")
        update_task_status(task_id, "failed", 0, error_msg)
        raise


@celery_app.task(bind=True, name="app.tasks.fetch_tasks.fetch_and_process_pipeline")
def fetch_and_process_pipeline(
    self, min_score: Optional[int] = None, keyword: Optional[str] = None, limit: int = 100
) -> Dict[str, Any]:
    """
    Complete pipeline: fetch top stories, get details, process and store.

    Args:
        min_score: Minimum score filter
        keyword: Keyword filter
        limit: Number of stories to fetch

    Returns:
        Pipeline results
    """
    task_id = self.request.id
    logger.info(f"Starting fetch_and_process_pipeline task {task_id}")

    try:
        # Step 1: Fetch top stories
        story_ids = fetch_top_stories(limit)
        update_task_status(task_id, "processing", 30, f"Fetched {len(story_ids)} story IDs")

        # Step 2: Fetch item details
        items = fetch_item_details(story_ids)
        update_task_status(task_id, "processing", 60, f"Fetched {len(items)} item details")

        # Step 3: Process and store
        result = process_and_store_items(items, min_score, keyword)
        update_task_status(task_id, "processing", 90, f"Processed and stored {result.get('items_stored', 0)} items")

        # Add pipeline metadata
        result["pipeline_task_id"] = task_id
        result["total_stories_fetched"] = len(story_ids)
        result["total_items_processed"] = len(items)

        logger.info(f"Pipeline task {task_id} completed: {result}")
        update_task_status(task_id, "completed", 100, "Pipeline completed successfully")

        return result

    except Exception as e:
        error_msg = f"Pipeline failed: {str(e)}"
        logger.error(f"Pipeline task {task_id} failed: {error_msg}")
        update_task_status(task_id, "failed", 0, error_msg)
        raise


@celery_app.task(bind=True, name="app.tasks.fetch_tasks.scheduled_fetch_task")
def scheduled_fetch_task(
    self, min_score: Optional[int] = None, keyword: Optional[str] = None, limit: int = 100
) -> Dict[str, Any]:
    """
    Scheduled task for periodic data fetching.

    Args:
        min_score: Minimum score filter
        keyword: Keyword filter
        limit: Number of stories to fetch

    Returns:
        Fetch results
    """
    task_id = self.request.id
    logger.info(f"Starting scheduled fetch task {task_id}")

    try:
        # Run the complete pipeline
        result = fetch_and_process_pipeline(min_score, keyword, limit)

        # Add scheduling metadata
        result["scheduled_task_id"] = task_id
        result["scheduled_at"] = datetime.now(timezone.utc).isoformat()

        logger.info(f"Scheduled task {task_id} completed: {result}")
        return result

    except Exception as e:
        error_msg = f"Scheduled task failed: {str(e)}"
        logger.error(f"Scheduled task {task_id} failed: {error_msg}")
        raise


def update_task_status(task_id: str, status: str, progress: int, message: str):
    """Update task status in cache."""
    try:
        task_status = cache.get(f"task:{task_id}")
        if not task_status:
            # Create initial task status if it doesn't exist
            task_status = {
                "task_id": task_id,
                "status": status,
                "progress": progress,
                "message": message,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
        else:
            # Update existing task status
            task_status.update(
                {
                    "status": status,
                    "progress": progress,
                    "message": message,
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                }
            )
        cache.set(f"task:{task_id}", task_status, ttl=3600)
    except Exception as e:
        logger.error(f"Failed to update task status for {task_id}: {e}")


def get_task_status(task_id: str) -> Optional[Dict[str, Any]]:
    """Get task status from cache."""
    try:
        return cache.get(f"task:{task_id}")
    except Exception as e:
        logger.error(f"Failed to get task status for {task_id}: {e}")
        return None
