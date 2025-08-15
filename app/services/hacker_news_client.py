import asyncio
import httpx
from typing import List, Optional, Dict, Any
from app.core.config import settings, cache_result


class HackerNewsAPIClient:
    """Client for interacting with Hacker News API."""

    def __init__(self):
        self.base_url = settings.hacker_news_api_base_url

    @cache_result(ttl=settings.cache_ttl_seconds, namespace="hn")
    async def get_top_stories(self, limit: int = 100) -> List[int]:
        """Get top stories IDs from Hacker News API."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/topstories.json")
                response.raise_for_status()
                all_story_ids = response.json()
                
                # Return limited number of story IDs
                story_ids = all_story_ids[:limit]
                return story_ids

        except Exception as e:
            # Log error and return empty list as fallback
            print(f"Error fetching top stories: {e}")
            return []

    # @cache_result(ttl=settings.cache_ttl_seconds, namespace="hn")
    async def get_item(self, item_id: int) -> Optional[Dict[str, Any]]:
        """Get item details from Hacker News API."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/item/{item_id}.json")
                response.raise_for_status()
                item_data = response.json()
                
                if item_data:
                    return self.transform_item_fields(item_data)
                
                return None

        except Exception as e:
            # Log error and return None as fallback
            print(f"Error fetching item {item_id}: {e}")
            return None

    async def get_items_batch(self, item_ids: List[int]) -> List[Dict[str, Any]]:
        """Get multiple items in batch."""
        tasks = [self.get_item(item_id) for item_id in item_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out None results and exceptions
        items = []
        for result in results:
            if isinstance(result, dict):
                items.append(result)

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


hacker_news_client = HackerNewsAPIClient()
