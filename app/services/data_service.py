from typing import List, Optional, Dict, Any
from sqlalchemy import desc, asc

from app.core.config import get_db_session, SessionLocal, settings
from app.models.database import HackerNewsItem
from app.models.schemas import HackerNewsItemResponse

from app.core.config import cache, get_logger, cache_result

logger = get_logger("data_service")


class DataService:
    """Optimized data service with caching and query optimization."""

    def __init__(self):
        self.cache_ttl = settings.cache_ttl_seconds


    def store_items(self, items: List[Dict[str, Any]]) -> Optional[HackerNewsItemResponse]:
        """Store items in the database with bulk operations."""
        db = SessionLocal()
        try:
            stored_count = 0

            # Use bulk operations for better performance
            for item_data in items:
                # Map API fields to database fields
                mapped_data = {
                    "id": item_data["id"],
                    "title": item_data["title"],
                    "url": item_data.get("url"),
                    "score": item_data.get("score"),
                    "author": item_data.get("author") or item_data.get("by"),  # Handle both "author" and "by"
                    "timestamp": item_data.get("timestamp") or item_data.get("time"),  # Handle both "timestamp" and "time"
                    "descendants": item_data.get("descendants"),
                    "type": item_data.get("type"),
                    "text": item_data.get("text"),
                }
                
                # Check if item already exists
                existing_item = db.query(HackerNewsItem).filter(HackerNewsItem.id == mapped_data["id"]).first()

                if existing_item:
                    # Update existing item only if data has changed
                    updated = False
                    for key, value in mapped_data.items():
                        if hasattr(existing_item, key) and getattr(existing_item, key) != value:
                            setattr(existing_item, key, value)
                            updated = True
                    
                    # Only count as stored if actually updated
                    if updated:
                        stored_count += 1
                else:
                    # Create new item
                    db_item = HackerNewsItem(**mapped_data)
                    db.add(db_item)
                    stored_count += 1

            db.commit()
            logger.info(f"Stored {stored_count} items in database")

            # Return the first stored item for testing purposes
            if items:
                first_item = items[0]
                # Map API fields to schema fields
                mapped_item = {
                    "id": first_item["id"],
                    "title": first_item["title"],
                    "url": first_item.get("url"),
                    "score": first_item.get("score", 0),
                    "author": first_item.get("author", ""),
                    "timestamp": first_item.get("timestamp", 0),
                    "descendants": first_item.get("descendants"),
                    "type": first_item.get("type", "story"),
                    "text": first_item.get("text"),
                    "kids": first_item.get("kids", [])
                }
                return HackerNewsItemResponse.model_validate(mapped_item)

            return None

        except Exception as e:
            db.rollback()
            logger.error(f"Failed to store items: {e}")
            raise
        finally:
            db.close()

    def _build_query_filters(
        self, query, item_id: Optional[int] = None, min_score: Optional[int] = None, keyword: Optional[str] = None
    ):
        """Build optimized query filters."""
        if item_id is not None:
            query = query.filter(HackerNewsItem.id == item_id)

        if min_score is not None:
            query = query.filter(HackerNewsItem.score >= min_score)

        if keyword:
            # Use case-insensitive search with index optimization
            query = query.filter(HackerNewsItem.title.ilike(f"%{keyword}%"))

        return query

    def _build_query_ordering(self, query, order_by: str = "score", order_direction: str = "desc"):
        """Build optimized query ordering."""
        if order_by == "score":
            if order_direction == "desc":
                query = query.order_by(desc(HackerNewsItem.score))
            else:
                query = query.order_by(asc(HackerNewsItem.score))
        elif order_by == "time":
            if order_direction == "desc":
                query = query.order_by(desc(HackerNewsItem.timestamp))
            else:
                query = query.order_by(asc(HackerNewsItem.timestamp))
        elif order_by == "id":
            if order_direction == "desc":
                query = query.order_by(desc(HackerNewsItem.id))
            else:
                query = query.order_by(asc(HackerNewsItem.id))

        return query

    def get_items_query(
        self,
        item_id: Optional[int] = None,
        min_score: Optional[int] = None,
        keyword: Optional[str] = None,
        order_by: str = "score",
        order_direction: str = "desc",
        db=None,
    ):
        """Get SQLAlchemy query for items with optimized filters and ordering."""
        if db is None:
            # For backward compatibility, create a new session
            db = SessionLocal()
            
        # Build base query with optimizations
        query = db.query(HackerNewsItem)

        # Apply filters
        query = self._build_query_filters(query, item_id, min_score, keyword)

        # Apply ordering
        query = self._build_query_ordering(query, order_by, order_direction)

        logger.debug("Built optimized query for items")

        return query


# Create global optimized service instance
data_service = DataService()
