import pytest
from app.models.orm import HackerNewsItem


class TestHackerNewsItemRepository:
    """Test repository layer with real SQLite in-memory database."""
    
    def test_create_item(self, db_session):
        """Test creating a new HackerNewsItem."""
        item = HackerNewsItem(
            id=12345,
            title="Test Story",
            url="https://example.com",
            score=100,
            author="testuser",
            timestamp=1640995200,
            descendants=10,
            type="story",
            text=None
        )
        
        db_session.add(item)
        db_session.commit()
        db_session.refresh(item)
        
        # Verify item was created
        assert item.id == 12345
        assert item.title == "Test Story"
        assert item.url == "https://example.com"
        assert item.score == 100
        assert item.author == "testuser"
        assert item.timestamp == 1640995200
        assert item.descendants == 10
        assert item.type == "story"
        assert item.text is None
        assert item.created_at is not None
        assert item.updated_at is not None
    
    def test_create_multiple_items(self, db_session):
        """Test creating multiple items."""
        items = [
            HackerNewsItem(id=1, title="Story 1", score=100, author="user1", timestamp=1640995200, type="story"),
            HackerNewsItem(id=2, title="Story 2", score=200, author="user2", timestamp=1640995300, type="story"),
            HackerNewsItem(id=3, title="Story 3", score=150, author="user3", timestamp=1640995400, type="story"),
        ]
        
        for item in items:
            db_session.add(item)
        db_session.commit()
        
        # Verify all items were created
        stored_items = db_session.query(HackerNewsItem).all()
        assert len(stored_items) == 3
        
        # Verify items are in correct order (by ID)
        assert stored_items[0].id == 1
        assert stored_items[1].id == 2
        assert stored_items[2].id == 3
    
    def test_find_item_by_id(self, db_session):
        """Test finding an item by its ID."""
        # Create test item
        item = HackerNewsItem(
            id=12345,
            title="Test Story",
            score=100,
            author="testuser",
            timestamp=1640995200,
            type="story"
        )
        db_session.add(item)
        db_session.commit()
        
        # Find the item
        found_item = db_session.query(HackerNewsItem).filter_by(id=12345).first()
        
        assert found_item is not None
        assert found_item.id == 12345
        assert found_item.title == "Test Story"
    
    def test_find_item_by_id_not_found(self, db_session):
        """Test finding an item that doesn't exist."""
        found_item = db_session.query(HackerNewsItem).filter_by(id=99999).first()
        assert found_item is None
    
    def test_update_item(self, db_session):
        """Test updating an existing item."""
        # Create test item
        item = HackerNewsItem(
            id=12345,
            title="Original Title",
            score=50,
            author="originaluser",
            timestamp=1640995000,
            type="story"
        )
        db_session.add(item)
        db_session.commit()
        
        # Update the item
        item.title = "Updated Title"
        item.score = 150
        item.author = "updateduser"
        db_session.commit()
        db_session.refresh(item)
        
        # Verify updates
        assert item.title == "Updated Title"
        assert item.score == 150
        assert item.author == "updateduser"
    
    def test_delete_item(self, db_session):
        """Test deleting an item."""
        # Create test item
        item = HackerNewsItem(
            id=12345,
            title="Test Story",
            score=100,
            author="testuser",
            timestamp=1640995200,
            type="story"
        )
        db_session.add(item)
        db_session.commit()
        
        # Verify item exists
        assert db_session.query(HackerNewsItem).filter_by(id=12345).first() is not None
        
        # Delete the item
        db_session.delete(item)
        db_session.commit()
        
        # Verify item was deleted
        assert db_session.query(HackerNewsItem).filter_by(id=12345).first() is None
    
    def test_query_items_by_score(self, db_session):
        """Test querying items by score filter."""
        # Create test items with different scores
        items = [
            HackerNewsItem(id=1, title="Low Score", score=50, author="user1", timestamp=1640995200, type="story"),
            HackerNewsItem(id=2, title="Medium Score", score=100, author="user2", timestamp=1640995300, type="story"),
            HackerNewsItem(id=3, title="High Score", score=200, author="user3", timestamp=1640995400, type="story"),
        ]
        
        for item in items:
            db_session.add(item)
        db_session.commit()
        
        # Query items with score >= 100
        high_score_items = db_session.query(HackerNewsItem).filter(HackerNewsItem.score >= 100).all()
        
        assert len(high_score_items) == 2
        assert high_score_items[0].id == 2
        assert high_score_items[1].id == 3
    
    def test_query_items_by_keyword(self, db_session):
        """Test querying items by keyword in title."""
        # Create test items with different titles
        items = [
            HackerNewsItem(id=1, title="Python Tutorial", score=100, author="user1", timestamp=1640995200, type="story"),
            HackerNewsItem(id=2, title="JavaScript Guide", score=100, author="user2", timestamp=1640995300, type="story"),
            HackerNewsItem(id=3, title="Python Best Practices", score=100, author="user3", timestamp=1640995400, type="story"),
        ]
        
        for item in items:
            db_session.add(item)
        db_session.commit()
        
        # Query items with "Python" in title
        python_items = db_session.query(HackerNewsItem).filter(
            HackerNewsItem.title.ilike("%Python%")
        ).all()
        
        assert len(python_items) == 2
        assert python_items[0].id == 1
        assert python_items[1].id == 3
    
    def test_query_items_ordered_by_score_desc(self, db_session):
        """Test querying items ordered by score descending."""
        # Create test items with different scores
        items = [
            HackerNewsItem(id=1, title="Low Score", score=50, author="user1", timestamp=1640995200, type="story"),
            HackerNewsItem(id=2, title="Medium Score", score=100, author="user2", timestamp=1640995300, type="story"),
            HackerNewsItem(id=3, title="High Score", score=200, author="user3", timestamp=1640995400, type="story"),
        ]
        
        for item in items:
            db_session.add(item)
        db_session.commit()
        
        # Query items ordered by score descending
        from sqlalchemy import desc
        ordered_items = db_session.query(HackerNewsItem).order_by(desc(HackerNewsItem.score)).all()
        
        assert len(ordered_items) == 3
        assert ordered_items[0].score == 200
        assert ordered_items[1].score == 100
        assert ordered_items[2].score == 50
    
    def test_query_items_ordered_by_timestamp_asc(self, db_session):
        """Test querying items ordered by timestamp ascending."""
        # Create test items with different timestamps
        items = [
            HackerNewsItem(id=1, title="Old Story", score=100, author="user1", timestamp=1640995200, type="story"),
            HackerNewsItem(id=2, title="New Story", score=100, author="user2", timestamp=1640995400, type="story"),
            HackerNewsItem(id=3, title="Middle Story", score=100, author="user3", timestamp=1640995300, type="story"),
        ]
        
        for item in items:
            db_session.add(item)
        db_session.commit()
        
        # Query items ordered by timestamp ascending
        from sqlalchemy import asc
        ordered_items = db_session.query(HackerNewsItem).order_by(asc(HackerNewsItem.timestamp)).all()
        
        assert len(ordered_items) == 3
        assert ordered_items[0].timestamp == 1640995200
        assert ordered_items[1].timestamp == 1640995300
        assert ordered_items[2].timestamp == 1640995400
    
    def test_query_items_with_multiple_filters(self, db_session):
        """Test querying items with multiple filters."""
        # Create test items
        items = [
            HackerNewsItem(id=1, title="Python Low Score", score=50, author="user1", timestamp=1640995200, type="story"),
            HackerNewsItem(id=2, title="Python High Score", score=150, author="user2", timestamp=1640995300, type="story"),
            HackerNewsItem(id=3, title="JavaScript High Score", score=150, author="user3", timestamp=1640995400, type="story"),
            HackerNewsItem(id=4, title="Python Medium Score", score=100, author="user4", timestamp=1640995500, type="story"),
        ]
        
        for item in items:
            db_session.add(item)
        db_session.commit()
        
        # Query items with score >= 100 AND title contains "Python"
        from sqlalchemy import desc
        filtered_items = db_session.query(HackerNewsItem).filter(
            HackerNewsItem.score >= 100,
            HackerNewsItem.title.ilike("%Python%")
        ).order_by(desc(HackerNewsItem.score)).all()
        
        assert len(filtered_items) == 2
        assert filtered_items[0].id == 2  # Python High Score (150)
        assert filtered_items[1].id == 4  # Python Medium Score (100)
    
    def test_count_items(self, db_session):
        """Test counting items in the database."""
        # Create test items
        items = [
            HackerNewsItem(id=1, title="Story 1", score=100, author="user1", timestamp=1640995200, type="story"),
            HackerNewsItem(id=2, title="Story 2", score=200, author="user2", timestamp=1640995300, type="story"),
            HackerNewsItem(id=3, title="Story 3", score=150, author="user3", timestamp=1640995400, type="story"),
        ]
        
        for item in items:
            db_session.add(item)
        db_session.commit()
        
        # Count all items
        total_count = db_session.query(HackerNewsItem).count()
        assert total_count == 3
        
        # Count items with score >= 150
        high_score_count = db_session.query(HackerNewsItem).filter(HackerNewsItem.score >= 150).count()
        assert high_score_count == 2
    
    def test_pagination(self, db_session):
        """Test pagination of query results."""
        # Create test items
        items = []
        for i in range(10):
            item = HackerNewsItem(
                id=i+1,
                title=f"Story {i+1}",
                score=100 + i,
                author=f"user{i+1}",
                timestamp=1640995200 + i,
                type="story"
            )
            items.append(item)
        
        for item in items:
            db_session.add(item)
        db_session.commit()
        
        # Test pagination: page 1, size 3
        page1_items = db_session.query(HackerNewsItem).order_by(HackerNewsItem.id).limit(3).offset(0).all()
        assert len(page1_items) == 3
        assert page1_items[0].id == 1
        assert page1_items[1].id == 2
        assert page1_items[2].id == 3
        
        # Test pagination: page 2, size 3
        page2_items = db_session.query(HackerNewsItem).order_by(HackerNewsItem.id).limit(3).offset(3).all()
        assert len(page2_items) == 3
        assert page2_items[0].id == 4
        assert page2_items[1].id == 5
        assert page2_items[2].id == 6
    
    def test_unique_constraint_violation(self, db_session):
        """Test that duplicate IDs are not allowed."""
        # Create first item
        item1 = HackerNewsItem(
            id=12345,
            title="First Story",
            score=100,
            author="user1",
            timestamp=1640995200,
            type="story"
        )
        db_session.add(item1)
        db_session.commit()
        
        # Try to create second item with same ID
        item2 = HackerNewsItem(
            id=12345,  # Same ID
            title="Second Story",
            score=200,
            author="user2",
            timestamp=1640995300,
            type="story"
        )
        db_session.add(item2)
        
        # Should raise an integrity error
        with pytest.raises(Exception):  # SQLAlchemy IntegrityError
            db_session.commit()
        
        # Rollback to clean state
        db_session.rollback()
    
    def test_nullable_fields(self, db_session):
        """Test that nullable fields can be None."""
        # Create item with some None values
        item = HackerNewsItem(
            id=12345,
            title="Test Story",  # Required field
            score=None,  # Nullable
            author=None,  # Nullable
            timestamp=None,  # Nullable
            type=None,  # Nullable
            url=None,  # Nullable
            descendants=None,  # Nullable
            text=None  # Nullable
        )
        
        db_session.add(item)
        db_session.commit()
        db_session.refresh(item)
        
        # Verify item was created with None values
        assert item.id == 12345
        assert item.title == "Test Story"
        assert item.score is None
        assert item.author is None
        assert item.timestamp is None
        assert item.type is None
        assert item.url is None
        assert item.descendants is None
        assert item.text is None
