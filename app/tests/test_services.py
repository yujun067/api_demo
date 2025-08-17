import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from app.services.data_service import DataService
from app.services.hacker_news_client import HackerNewsAPIClient
from app.models.orm import HackerNewsItem
from app.models.api import StoreItemsResponse


class TestDataService:
    """Test DataService with fake database and mocked external dependencies."""
    
    def test_store_items_new_items(self, fake_data_service, db_session, sample_hacker_news_items):
        """Test storing new items in database."""
        service = fake_data_service
        
        items = sample_hacker_news_items[:2]  # Use first 2 items from fixture
        
        result = service.store_items(items, db_session)
        
        # Verify items were stored
        stored_items = db_session.query(HackerNewsItem).all()
        assert len(stored_items) == 2
        assert stored_items[0].id == 1
        assert stored_items[0].title == "Test Story 1"
        assert stored_items[1].id == 2
        assert stored_items[1].title == "Test Story 2"
        
        # Verify return value
        assert isinstance(result, StoreItemsResponse)
        assert result.stored_count == 2
        assert result.new_items == 2
        assert result.updated_items == 0
    
    def test_store_items_existing_items_update(self, fake_data_service, db_session):
        """Test storing items that already exist (should update)."""
        service = fake_data_service
        
        # Create existing item
        existing_item = HackerNewsItem(
            id=1,
            title="Old Title",
            url="https://old.com",
            score=50,
            author="olduser",
            timestamp=1640995000,
            descendants=5,
            type="story",
            text=None
        )
        db_session.add(existing_item)
        db_session.commit()
        
        # New data for the same item (using API field names to test mapping)
        items = [
            {
                "id": 1,
                "title": "New Title",
                "url": "https://new.com",
                "score": 100,
                "author": "newuser",
                "timestamp": 1640995200,
                "descendants": 10,
                "type": "story",
                "text": None
            }
        ]
        
        result = service.store_items(items, db_session)
        
        # Verify item was updated
        updated_item = db_session.query(HackerNewsItem).filter_by(id=1).first()
        assert updated_item.title == "New Title"
        assert updated_item.url == "https://new.com"
        assert updated_item.score == 100
        assert updated_item.author == "newuser"
        
        # Verify return value
        assert isinstance(result, StoreItemsResponse)
        assert result.stored_count == 1
        assert result.new_items == 0
        assert result.updated_items == 1
    
    def test_store_items_existing_items_no_changes(self, fake_data_service, db_session):
        """Test storing items that exist but haven't changed."""
        service = fake_data_service
        
        # Create existing item
        existing_item = HackerNewsItem(
            id=1,
            title="Test Title",
            url="https://example.com",
            score=100,
            author="testuser",
            timestamp=1640995200,
            descendants=10,
            type="story",
            text=None
        )
        db_session.add(existing_item)
        db_session.commit()
        
        # Same data
        items = [
            {
                "id": 1,
                "title": "Test Title",
                "url": "https://example.com",
                "score": 100,
                "author": "testuser",
                "timestamp": 1640995200,
                "descendants": 10,
                "type": "story",
                "text": None
            }
        ]
        
        result = service.store_items(items, db_session)
        
        # Verify item wasn't changed
        item = db_session.query(HackerNewsItem).filter_by(id=1).first()
        assert item.title == "Test Title"
        
        # Verify return value
        assert isinstance(result, StoreItemsResponse)
        assert result.stored_count == 0
        assert result.new_items == 0
        assert result.updated_items == 0
    
    def test_store_items_empty_list(self, fake_data_service, db_session):
        """Test storing empty list of items."""
        service = fake_data_service
        
        result = service.store_items([], db_session)
        
        # Verify no items were stored
        stored_items = db_session.query(HackerNewsItem).all()
        assert len(stored_items) == 0
        
        # Verify return value
        assert isinstance(result, StoreItemsResponse)
        assert result.stored_count == 0
        assert result.new_items == 0
        assert result.updated_items == 0
    
    def test_store_items_database_error(self, fake_data_service, db_session):
        """Test handling database errors during storage."""
        service = fake_data_service
        
        items = [
            {
                "id": 1,
                "title": "Test Story",
                "score": 100,
                "author": "testuser",
                "timestamp": 1640995200,
                "type": "story"
            }
        ]
        
        # Mock the database session to raise an exception
        with patch.object(db_session, 'commit') as mock_commit:
            mock_commit.side_effect = Exception("Database error")
            
            with pytest.raises(Exception, match="Database error"):
                service.store_items(items, db_session)
    
    def test_get_items_query_basic(self, fake_data_service, db_session):
        """Test building basic query without filters."""
        service = fake_data_service
        
        # Add some test data
        items = [
            HackerNewsItem(id=1, title="Story 1", score=100, author="user1", timestamp=1640995200, type="story"),
            HackerNewsItem(id=2, title="Story 2", score=200, author="user2", timestamp=1640995300, type="story"),
        ]
        for item in items:
            db_session.add(item)
        db_session.commit()
        
        # Use the db_session directly
        query = service.get_items_query(db_session)
        results = query.all()
        
        assert len(results) == 2
        assert results[0].id == 2  # Default order by score desc
        assert results[1].id == 1
    
    def test_get_items_query_with_filters(self, fake_data_service, db_session):
        """Test building query with filters."""
        service = fake_data_service
        
        # Add test data
        items = [
            HackerNewsItem(id=1, title="Python Story", score=50, author="user1", timestamp=1640995200, type="story"),
            HackerNewsItem(id=2, title="JavaScript Story", score=100, author="user2", timestamp=1640995300, type="story"),
            HackerNewsItem(id=3, title="Python Guide", score=150, author="user3", timestamp=1640995400, type="story"),
        ]
        for item in items:
            db_session.add(item)
        db_session.commit()
        
        # Use the db_session directly
        query = service.get_items_query(
            db_session,
            min_score=100,
            keyword="Python",
            order_by="score",
            order_direction="desc"
        )
        results = query.all()
        
        assert len(results) == 1
        assert results[0].id == 3  # Only Python Guide with score >= 100
        assert results[0].title == "Python Guide"
    
    def test_get_items_query_by_id(self, fake_data_service, db_session):
        """Test building query to get specific item by ID."""
        service = fake_data_service
        
        # Add test data
        item = HackerNewsItem(id=123, title="Specific Story", score=100, author="user1", timestamp=1640995200, type="story")
        db_session.add(item)
        db_session.commit()
        
        # Use the db_session directly
        query = service.get_items_query(db_session, item_id=123)
        results = query.all()
        
        assert len(results) == 1
        assert results[0].id == 123
        assert results[0].title == "Specific Story"


class TestHackerNewsAPIClient:
    """Test HackerNewsAPIClient with mocked external API calls."""
    
    @pytest.mark.asyncio
    async def test_get_top_stories_success(self):
        """Test successful API call to get top stories."""
        client = HackerNewsAPIClient()
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = MagicMock()
            mock_response.json.return_value = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
            mock_response.raise_for_status.return_value = None
            
            mock_client_instance = AsyncMock()
            mock_client_instance.__aenter__.return_value = mock_client_instance
            mock_client_instance.__aexit__.return_value = None
            mock_client_instance.get.return_value = mock_response
            mock_client.return_value = mock_client_instance
            
            result = await client.get_top_stories(limit=5)
        
        assert result == [1, 2, 3, 4, 5]
        mock_client_instance.get.assert_called_once_with(f"{client.base_url}/topstories.json")
    
    @pytest.mark.asyncio
    async def test_get_top_stories_api_error(self):
        """Test handling API errors when getting top stories."""
        client = HackerNewsAPIClient()
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client_instance = AsyncMock()
            mock_client_instance.__aenter__.return_value = mock_client_instance
            mock_client_instance.__aexit__.return_value = None
            mock_client_instance.get.side_effect = Exception("API Error")
            mock_client.return_value = mock_client_instance
            
            with pytest.raises(Exception, match="API Error"):
                await client.get_top_stories()
    
    @pytest.mark.asyncio
    async def test_get_item_success(self):
        """Test successful API call to get item details."""
        client = HackerNewsAPIClient()
        
        expected_item = {
            "id": 123,
            "title": "Test Story",
            "url": "https://example.com",
            "score": 100,
            "author": "testuser",
            "timestamp": 1640995200,
            "descendants": 10,
            "type": "story",
            "text": None
        }
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = MagicMock()
            mock_response.json.return_value = expected_item
            mock_response.raise_for_status.return_value = None
            
            mock_client_instance = AsyncMock()
            mock_client_instance.__aenter__.return_value = mock_client_instance
            mock_client_instance.__aexit__.return_value = None
            mock_client_instance.get.return_value = mock_response
            mock_client.return_value = mock_client_instance
            
            result = await client.get_item(123)
        
        assert result == expected_item
        mock_client_instance.get.assert_called_once_with(f"{client.base_url}/item/123.json")
    
    @pytest.mark.asyncio
    async def test_get_item_not_found(self):
        """Test handling item not found."""
        client = HackerNewsAPIClient()
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = MagicMock()
            mock_response.json.return_value = None
            mock_response.raise_for_status.return_value = None
            
            mock_client_instance = AsyncMock()
            mock_client_instance.__aenter__.return_value = mock_client_instance
            mock_client_instance.__aexit__.return_value = None
            mock_client_instance.get.return_value = mock_response
            mock_client.return_value = mock_client_instance
            
            result = await client.get_item(999)
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_item_api_error(self):
        """Test handling API errors when getting item."""
        client = HackerNewsAPIClient()
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client_instance = AsyncMock()
            mock_client_instance.__aenter__.return_value = mock_client_instance
            mock_client_instance.__aexit__.return_value = None
            mock_client_instance.get.side_effect = Exception("API Error")
            mock_client.return_value = mock_client_instance
            
            with pytest.raises(Exception, match="API Error"):
                await client.get_item(123)
    
    @pytest.mark.asyncio
    async def test_get_items_batch_success(self):
        """Test successful batch API calls."""
        client = HackerNewsAPIClient()
        
        with patch.object(client, 'get_item') as mock_get_item:
            async def mock_get_item_async(*args, **kwargs):
                if args[0] == 1:
                    return {"id": 1, "title": "Story 1"}
                elif args[0] == 2:
                    return {"id": 2, "title": "Story 2"}
                elif args[0] == 3:
                    return None
                elif args[0] == 4:
                    return {"id": 4, "title": "Story 4"}
                return None
            
            mock_get_item.side_effect = mock_get_item_async
            
            result = await client.get_items_batch([1, 2, 3, 4])
        
        assert len(result) == 3
        assert result[0]["id"] == 1
        assert result[1]["id"] == 2
        assert result[2]["id"] == 4
    
    @pytest.mark.asyncio
    async def test_get_items_batch_with_exceptions(self):
        """Test batch API calls with some exceptions."""
        client = HackerNewsAPIClient()
        
        with patch.object(client, 'get_item') as mock_get_item:
            async def mock_get_item_async(*args, **kwargs):
                if args[0] == 1:
                    return {"id": 1, "title": "Story 1"}
                elif args[0] == 2:
                    raise Exception("API Error")
                elif args[0] == 3:
                    return {"id": 3, "title": "Story 3"}
                return None
            
            mock_get_item.side_effect = mock_get_item_async
            
            result = await client.get_items_batch([1, 2, 3])
        
        assert len(result) == 2
        assert result[0]["id"] == 1
        assert result[1]["id"] == 3
