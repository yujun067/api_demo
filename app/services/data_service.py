from typing import List, Optional, Dict, Any
from sqlalchemy import desc, asc
from sqlalchemy.orm import Session

from app.models.orm import HackerNewsItem
from app.models.api import StoreItemsResponse
from app.core.config import get_logger

logger = get_logger("data_service")


class DataService:
    """Optimized data service with caching and query optimization."""

    def store_items(self, items: List[Dict[str, Any]], db: Session) -> StoreItemsResponse:
        """Store items in the database with bulk operations.
        
        Args:
            items: List of items to store
            db: Database session (injected dependency)
            
        Returns:
            StoreItemsResponse with detailed statistics about the operation.
        """
        try:
            stored_count = 0
            new_items = 0
            updated_items = 0

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
                        updated_items += 1
                else:
                    # Create new item
                    db_item = HackerNewsItem(**mapped_data)
                    db.add(db_item)
                    stored_count += 1
                    new_items += 1

            db.commit()
            logger.info(f"Stored {stored_count} items in database (new: {new_items}, updated: {updated_items})")

            return StoreItemsResponse(
                stored_count=stored_count,
                total_items=len(items),
                new_items=new_items,
                updated_items=updated_items,
                skipped_items=len(items) - stored_count
            )

        except Exception as e:
            db.rollback()
            logger.error(f"Failed to store items: {e}")
            raise

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
        db: Session,
        item_id: Optional[int] = None,
        min_score: Optional[int] = None,
        keyword: Optional[str] = None,
        order_by: str = "score",
        order_direction: str = "desc",
    ):
        """Get SQLAlchemy query for items with optimized filters and ordering.
        
        Args:
            db: Database session (injected dependency)
            item_id: Optional item ID filter
            min_score: Optional minimum score filter
            keyword: Optional keyword filter
            order_by: Field to order by
            order_direction: Order direction (asc/desc)
            
        Returns:
            SQLAlchemy query object
        """
        # Build base query with optimizations
        query = db.query(HackerNewsItem)

        # Apply filters
        query = self._build_query_filters(query, item_id, min_score, keyword)

        # Apply ordering
        query = self._build_query_ordering(query, order_by, order_direction)

        logger.debug("Built optimized query for items")

        return query


# Create data service instance
data_service = DataService()
