import asyncio
import httpx
from typing import List, Optional, Dict, Any
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from app.core.config import settings, cache_result, get_logger


logger = get_logger("hacker_news_client")


class HackerNewsAPIClient:
    """Client for interacting with Hacker News API."""

    def __init__(self):
        self.base_url = settings.hacker_news_api_base_url

    @cache_result(ttl=settings.cache_ttl_seconds, namespace="hn")
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=5),
        retry=retry_if_exception_type((httpx.ConnectError, httpx.TimeoutException))
    )
    async def get_top_stories(self, limit: int = 100) -> List[int]:
        """Get top stories IDs from Hacker News API."""
        url = f"{self.base_url}/topstories.json"
        logger.info(f"Fetching top stories with limit={limit}")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(url)
                response.raise_for_status()
                all_story_ids = response.json()
                story_ids = all_story_ids[:limit]
                logger.info(f"Successfully fetched {len(story_ids)} story IDs")
                return story_ids
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error fetching top stories: {e.response.status_code}")
                raise
            except httpx.RequestError as e:
                logger.error(f"Request error fetching top stories: {e}")
                raise

    @cache_result(ttl=settings.cache_ttl_seconds, namespace="hn")
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=5),
        retry=retry_if_exception_type((httpx.ConnectError, httpx.TimeoutException))
    )
    async def get_item(self, item_id: int) -> Optional[Dict[str, Any]]:
        """Get item details from Hacker News API."""
        url = f"{self.base_url}/item/{item_id}.json"
        logger.debug(f"Fetching item {item_id}")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(url)
                response.raise_for_status()
                item_data = response.json()
                
                if item_data:
                    transformed_item = self.transform_item_fields(item_data)
                    logger.debug(f"Successfully fetched item {item_id}")
                    return transformed_item
                return None
            except httpx.HTTPStatusError as e:
                logger.warning(f"HTTP error fetching item {item_id}: {e.response.status_code}")
                raise
            except httpx.RequestError as e:
                logger.warning(f"Request error fetching item {item_id}: {e}")
                raise

    async def get_items_batch(self, item_ids: List[int]) -> List[Dict[str, Any]]:
        """Get multiple items in batch with controlled concurrency."""
        logger.info(f"Fetching {len(item_ids)} items in batch")
        # add latency between batches
        # await asyncio.sleep(1)

        # Use semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(settings.max_concurrent_requests)
        
        async def fetch_with_semaphore(item_id: int) -> Optional[Dict[str, Any]]:
            async with semaphore:
                try:
                    return await self.get_item(item_id)
                except Exception as e:
                    logger.warning(f"Failed to fetch item {item_id}: {e}")
                    return None
        
        tasks = [fetch_with_semaphore(item_id) for item_id in item_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)
    
        # Filter out None results and exceptions
        items = []
        for i, result in enumerate(results):
            if isinstance(result, dict):
                items.append(result)
            elif isinstance(result, Exception):
                logger.warning(f"Exception fetching item {item_ids[i]}: {result}")
            else:
                logger.debug(f"Item {item_ids[i]} returned None")

        logger.info(f"Successfully fetched {len(items)} out of {len(item_ids)} items")
        return items

    def transform_item_fields(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Transform API response fields to match our database schema."""
        transformed = item.copy()
        
        # Transform "by" to "author"
        if "by" in transformed:
            transformed["author"] = transformed.pop("by")
        
        # Transform "time" to "timestamp"
        if "time" in transformed:
            transformed["timestamp"] = transformed.pop("time")
        
        return transformed

    def filter_items(
        self, items: List[Dict[str, Any]], min_score: Optional[int] = None, keyword: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Filter items based on criteria."""
        # Transform all items first
        transformed_items = [self.transform_item_fields(item) for item in items]
        
        filtered_items = transformed_items

        # Filter by minimum score
        if min_score is not None:
            filtered_items = [item for item in filtered_items if item.get("score", 0) >= min_score]

        # Filter by keyword in title
        if keyword:
            keyword_lower = keyword.lower()
            filtered_items = [item for item in filtered_items if keyword_lower in item.get("title", "").lower()]

        return filtered_items


# Create hacker news client instance
hacker_news_client = HackerNewsAPIClient()
