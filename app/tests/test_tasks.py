from unittest.mock import patch, AsyncMock, MagicMock
import pytest
from app.tasks.fetch_tasks import (
    fetch_top_stories,
    fetch_item_details,
    process_and_store_items,
    fetch_and_process_pipeline,
    scheduled_fetch_task,
    update_task_status,
    get_task_status
)


class TestFetchTopStoriesTask:
    """Test fetch_top_stories Celery task."""

    def test_fetch_top_stories_success(self, celery_test_app):
        """Test successful fetch_top_stories task execution."""
        with patch('app.tasks.fetch_tasks.hacker_news_client') as mock_client:
            mock_client.get_top_stories = AsyncMock(return_value=[1, 2, 3, 4, 5])
            
            # Execute the task
            result = fetch_top_stories(limit=5)
        
        assert result == [1, 2, 3, 4, 5]
        mock_client.get_top_stories.assert_called_once_with(limit=5)

    def test_fetch_top_stories_with_default_limit(self, celery_test_app):
        """Test fetch_top_stories with default limit."""
        with patch('app.tasks.fetch_tasks.hacker_news_client') as mock_client:
            mock_client.get_top_stories = AsyncMock(return_value=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
            
            result = fetch_top_stories()
        
        assert result == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        mock_client.get_top_stories.assert_called_once_with(limit=100)

    def test_fetch_top_stories_api_error(self, celery_test_app):
        """Test fetch_top_stories when API call fails."""
        with patch('app.tasks.fetch_tasks.hacker_news_client') as mock_client:
            mock_client.get_top_stories = AsyncMock(side_effect=Exception("API Error"))
            
            with pytest.raises(Exception, match="API Error"):
                fetch_top_stories(limit=5)

    def test_fetch_top_stories_empty_result(self, celery_test_app):
        """Test fetch_top_stories when API returns empty list."""
        with patch('app.tasks.fetch_tasks.hacker_news_client') as mock_client:
            mock_client.get_top_stories = AsyncMock(return_value=[])
            
            result = fetch_top_stories(limit=5)
        
        assert result == []


class TestFetchItemDetailsTask:
    """Test fetch_item_details Celery task."""

    def test_fetch_item_details_success(self, celery_test_app):
        """Test successful fetch_item_details task execution."""
        with patch('app.tasks.fetch_tasks.hacker_news_client') as mock_client:
            mock_client.get_items_batch = AsyncMock(return_value=[
                {"id": 1, "title": "Story 1", "score": 100},
                {"id": 2, "title": "Story 2", "score": 200}
            ])
            
            result = fetch_item_details([1, 2])
        
        assert len(result) == 2
        assert result[0]["id"] == 1
        assert result[1]["id"] == 2
        mock_client.get_items_batch.assert_called_once_with([1, 2])

    def test_fetch_item_details_empty_list(self, celery_test_app):
        """Test fetch_item_details with empty item IDs list."""
        with patch('app.tasks.fetch_tasks.hacker_news_client') as mock_client:
            mock_client.get_items_batch = AsyncMock(return_value=[])
            
            result = fetch_item_details([])
        
        assert result == []
        mock_client.get_items_batch.assert_called_once_with([])

    def test_fetch_item_details_api_error(self, celery_test_app):
        """Test fetch_item_details when API call fails."""
        with patch('app.tasks.fetch_tasks.hacker_news_client') as mock_client:
            mock_client.get_items_batch = AsyncMock(side_effect=Exception("API Error"))
            
            with pytest.raises(Exception, match="API Error"):
                fetch_item_details([1, 2])

    def test_fetch_item_details_partial_failure(self, celery_test_app):
        """Test fetch_item_details when some items fail to fetch."""
        with patch('app.tasks.fetch_tasks.hacker_news_client') as mock_client:
            # Mock that some items return None (failed to fetch)
            mock_client.get_items_batch = AsyncMock(return_value=[
                {"id": 1, "title": "Story 1", "score": 100},
                None,  # Failed to fetch
                {"id": 3, "title": "Story 3", "score": 300}
            ])
            
            result = fetch_item_details([1, 2, 3])
        
        assert len(result) == 3
        assert result[0]["id"] == 1
        assert result[1] is None
        assert result[2]["id"] == 3


class TestProcessAndStoreItemsTask:
    """Test process_and_store_items Celery task."""

    def test_process_and_store_items_success(self, celery_test_app, mock_session_local_for_tasks):
        """Test successful process_and_store_items task execution."""
        items = [
            {"id": 1, "title": "Story 1", "score": 100, "author": "user1"},
            {"id": 2, "title": "Story 2", "score": 200, "author": "user2"}
        ]
        
        with patch('app.tasks.fetch_tasks.hacker_news_client') as mock_client:
            mock_client.filter_items.return_value = items
            
            with patch('app.tasks.fetch_tasks.data_service') as mock_service:
                mock_response = MagicMock()
                mock_response.stored_count = 2
                mock_response.new_items = 2
                mock_response.updated_items = 0
                mock_service.store_items.return_value = mock_response
                
                result = process_and_store_items(items, min_score=50, keyword="test")
        
        assert result["items_processed"] == 2
        assert result["items_filtered"] == 2
        assert result["items_stored"] == 2
        assert result["new_items"] == 2
        assert result["updated_items"] == 0
        assert result["filters_applied"]["min_score"] == 50
        assert result["filters_applied"]["keyword"] == "test"

    def test_process_and_store_items_empty_list(self, celery_test_app, mock_session_local_for_tasks):
        """Test process_and_store_items with empty items list."""
        with patch('app.tasks.fetch_tasks.hacker_news_client') as mock_client:
            mock_client.filter_items.return_value = []
            
            with patch('app.tasks.fetch_tasks.data_service') as mock_service:
                mock_response = MagicMock()
                mock_response.stored_count = 0
                mock_response.new_items = 0
                mock_response.updated_items = 0
                mock_service.store_items.return_value = mock_response
                
                result = process_and_store_items([], min_score=50, keyword="test")
        
        assert result["items_processed"] == 0
        assert result["items_filtered"] == 0
        assert result["items_stored"] == 0

    def test_process_and_store_items_with_filters(self, celery_test_app, mock_session_local_for_tasks):
        """Test process_and_store_items with filtering applied."""
        items = [
            {"id": 1, "title": "Python Story", "score": 100, "author": "user1"},
            {"id": 2, "title": "JavaScript Story", "score": 50, "author": "user2"},
            {"id": 3, "title": "Python Guide", "score": 150, "author": "user3"}
        ]
        
        with patch('app.tasks.fetch_tasks.hacker_news_client') as mock_client:
            # Mock filtering to return only Python stories with score >= 100
            mock_client.filter_items.return_value = [
                {"id": 1, "title": "Python Story", "score": 100, "author": "user1"},
                {"id": 3, "title": "Python Guide", "score": 150, "author": "user3"}
            ]
            
            with patch('app.tasks.fetch_tasks.data_service') as mock_service:
                mock_response = MagicMock()
                mock_response.stored_count = 2
                mock_response.new_items = 2
                mock_response.updated_items = 0
                mock_service.store_items.return_value = mock_response
                
                result = process_and_store_items(items, min_score=100, keyword="Python")
        
        assert result["items_processed"] == 3
        assert result["items_filtered"] == 2
        assert result["items_stored"] == 2
        assert result["filters_applied"]["min_score"] == 100
        assert result["filters_applied"]["keyword"] == "Python"

    def test_process_and_store_items_database_error(self, celery_test_app, mock_session_local_for_tasks):
        """Test process_and_store_items when database operations fail."""
        items = [{"id": 1, "title": "Story 1", "score": 100}]
        
        with patch('app.tasks.fetch_tasks.hacker_news_client') as mock_client:
            mock_client.filter_items.return_value = items
            
            with patch('app.tasks.fetch_tasks.data_service') as mock_service:
                mock_service.store_items.side_effect = Exception("Database error")
                
                with pytest.raises(Exception, match="Database error"):
                    process_and_store_items(items)


class TestFetchAndProcessPipelineTask:
    """Test fetch_and_process_pipeline Celery task."""

    def test_fetch_and_process_pipeline_success(self, celery_test_app):
        """Test successful pipeline execution."""
        # Mock all the sub-tasks
        with patch('app.tasks.fetch_tasks.fetch_top_stories') as mock_fetch_stories:
            mock_fetch_stories.return_value = [1, 2, 3]
            
            with patch('app.tasks.fetch_tasks.fetch_item_details') as mock_fetch_details:
                mock_fetch_details.return_value = [
                    {"id": 1, "title": "Story 1", "score": 100},
                    {"id": 2, "title": "Story 2", "score": 200},
                    {"id": 3, "title": "Story 3", "score": 150}
                ]
                
                with patch('app.tasks.fetch_tasks.process_and_store_items') as mock_process:
                    mock_process.return_value = {
                        "items_processed": 3,
                        "items_filtered": 2,
                        "items_stored": 2,
                        "new_items": 2,
                        "updated_items": 0,
                        "filters_applied": {"min_score": 100, "keyword": None}
                    }
                    
                    with patch('app.tasks.fetch_tasks.update_task_status') as mock_update:
                        result = fetch_and_process_pipeline(min_score=100, keyword=None, limit=3)
        
        expected_result = {
            "items_processed": 3,
            "items_filtered": 2,
            "items_stored": 2,
            "new_items": 2,
            "updated_items": 0,
            "filters_applied": {"min_score": 100, "keyword": None},
            "pipeline_task_id": result["pipeline_task_id"],  # Use actual task ID
            "total_stories_fetched": 3,
            "total_items_processed": 3
        }
        
        assert result == expected_result

    def test_fetch_and_process_pipeline_with_filters(self, celery_test_app):
        """Test pipeline execution with filtering parameters."""
        with patch('app.tasks.fetch_tasks.fetch_top_stories') as mock_fetch_stories:
            mock_fetch_stories.return_value = [1, 2, 3, 4, 5]
            
            with patch('app.tasks.fetch_tasks.fetch_item_details') as mock_fetch_details:
                mock_fetch_details.return_value = [
                    {"id": 1, "title": "Python Story", "score": 100},
                    {"id": 2, "title": "JavaScript Story", "score": 50},
                    {"id": 3, "title": "Python Guide", "score": 150},
                    {"id": 4, "title": "Java Story", "score": 80},
                    {"id": 5, "title": "Python Tutorial", "score": 200}
                ]
                
                with patch('app.tasks.fetch_tasks.process_and_store_items') as mock_process:
                    mock_process.return_value = {
                        "items_processed": 5,
                        "items_filtered": 3,
                        "items_stored": 3,
                        "new_items": 3,
                        "updated_items": 0,
                        "filters_applied": {"min_score": 100, "keyword": "Python"}
                    }
                    
                    with patch('app.tasks.fetch_tasks.update_task_status') as mock_update:
                        result = fetch_and_process_pipeline(min_score=100, keyword="Python", limit=5)
        
        assert result["items_processed"] == 5
        assert result["items_filtered"] == 3
        assert result["items_stored"] == 3
        assert result["filters_applied"]["min_score"] == 100
        assert result["filters_applied"]["keyword"] == "Python"

    def test_fetch_and_process_pipeline_fetch_error(self, celery_test_app):
        """Test pipeline when fetch_top_stories fails."""
        with patch('app.tasks.fetch_tasks.fetch_top_stories') as mock_fetch_stories:
            mock_fetch_stories.side_effect = Exception("Fetch error")
            
            with patch('app.tasks.fetch_tasks.update_task_status') as mock_update:
                with pytest.raises(Exception, match="Fetch error"):
                    fetch_and_process_pipeline()

    def test_fetch_and_process_pipeline_details_error(self, celery_test_app):
        """Test pipeline when fetch_item_details fails."""
        with patch('app.tasks.fetch_tasks.fetch_top_stories') as mock_fetch_stories:
            mock_fetch_stories.return_value = [1, 2, 3]
            
            with patch('app.tasks.fetch_tasks.fetch_item_details') as mock_fetch_details:
                mock_fetch_details.side_effect = Exception("Details error")
                
                with patch('app.tasks.fetch_tasks.update_task_status') as mock_update:
                    with pytest.raises(Exception, match="Details error"):
                        fetch_and_process_pipeline()

    def test_fetch_and_process_pipeline_process_error(self, celery_test_app):
        """Test pipeline when process_and_store_items fails."""
        with patch('app.tasks.fetch_tasks.fetch_top_stories') as mock_fetch_stories:
            mock_fetch_stories.return_value = [1, 2, 3]
            
            with patch('app.tasks.fetch_tasks.fetch_item_details') as mock_fetch_details:
                mock_fetch_details.return_value = [{"id": 1, "title": "Story 1"}]
                
                with patch('app.tasks.fetch_tasks.process_and_store_items') as mock_process:
                    mock_process.side_effect = Exception("Process error")
                    
                    with patch('app.tasks.fetch_tasks.update_task_status') as mock_update:
                        with pytest.raises(Exception, match="Process error"):
                            fetch_and_process_pipeline()


class TestScheduledFetchTask:
    """Test scheduled_fetch_task Celery task."""

    def test_scheduled_fetch_task_success(self, celery_test_app):
        """Test successful scheduled fetch task execution."""
        with patch('app.tasks.fetch_tasks.fetch_and_process_pipeline') as mock_pipeline:
            mock_pipeline.return_value = {
                "items_processed": 10,
                "items_filtered": 8,
                "items_stored": 8,
                "new_items": 8,
                "updated_items": 0,
                "filters_applied": {"min_score": 50, "keyword": "AI"}
            }
            
            result = scheduled_fetch_task(min_score=50, keyword="AI", limit=100)
        
        expected_result = {
            "items_processed": 10,
            "items_filtered": 8,
            "items_stored": 8,
            "new_items": 8,
            "updated_items": 0,
            "filters_applied": {"min_score": 50, "keyword": "AI"},
            "scheduled_task_id": result["scheduled_task_id"],  # Use actual task ID
            "scheduled_at": result["scheduled_at"]  # This will be set by the task
        }
        
        assert result["items_processed"] == expected_result["items_processed"]
        assert result["scheduled_task_id"] == expected_result["scheduled_task_id"]
        assert "scheduled_at" in result

    def test_scheduled_fetch_task_with_filters(self, celery_test_app):
        """Test scheduled fetch task with filtering parameters."""
        with patch('app.tasks.fetch_tasks.fetch_and_process_pipeline') as mock_pipeline:
            mock_pipeline.return_value = {
                "items_processed": 5,
                "items_filtered": 3,
                "items_stored": 3,
                "new_items": 3,
                "updated_items": 0,
                "filters_applied": {"min_score": 100, "keyword": "Python"}
            }
            
            result = scheduled_fetch_task(min_score=100, keyword="Python", limit=50)
        
        assert result["items_processed"] == 5
        assert result["items_filtered"] == 3
        assert result["items_stored"] == 3
        assert result["filters_applied"]["min_score"] == 100
        assert result["filters_applied"]["keyword"] == "Python"

    def test_scheduled_fetch_task_pipeline_error(self, celery_test_app):
        """Test scheduled fetch task when pipeline fails."""
        with patch('app.tasks.fetch_tasks.fetch_and_process_pipeline') as mock_pipeline:
            mock_pipeline.side_effect = Exception("Pipeline error")
            
            with pytest.raises(Exception, match="Pipeline error"):
                scheduled_fetch_task()


class TestTaskStatusManagement:
    """Test task status management functions."""

    def test_update_task_status(self, celery_test_app):
        """Test updating task status."""
        with patch('app.tasks.fetch_tasks.cache') as mock_cache:
            mock_cache.get.return_value = None  # No existing status
            
            update_task_status("test-task-id", "processing", 50, "Processing items")
            
            # Verify cache.set was called with correct data
            mock_cache.set.assert_called_once()
            call_args = mock_cache.set.call_args
            assert call_args[0][0] == "task:test-task-id"
            assert call_args[0][1]["task_id"] == "test-task-id"
            assert call_args[0][1]["status"] == "processing"
            assert call_args[0][1]["progress"] == 50
            assert call_args[0][1]["message"] == "Processing items"

    def test_update_task_status_existing(self, celery_test_app):
        """Test updating existing task status."""
        existing_status = {
            "task_id": "test-task-id",
            "status": "processing",
            "progress": 30,
            "message": "Initial processing",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        }
        
        with patch('app.tasks.fetch_tasks.cache') as mock_cache:
            mock_cache.get.return_value = existing_status
            
            update_task_status("test-task-id", "completed", 100, "Task completed")
            
            # Verify cache.set was called with updated data
            mock_cache.set.assert_called_once()
            call_args = mock_cache.set.call_args
            updated_status = call_args[0][1]
            assert updated_status["status"] == "completed"
            assert updated_status["progress"] == 100
            assert updated_status["message"] == "Task completed"
            assert updated_status["created_at"] == "2024-01-01T00:00:00Z"  # Should not change

    def test_get_task_status(self, celery_test_app):
        """Test getting task status."""
        expected_status = {
            "task_id": "test-task-id",
            "status": "completed",
            "progress": 100,
            "message": "Task completed"
        }
        
        with patch('app.tasks.fetch_tasks.cache') as mock_cache:
            mock_cache.get.return_value = expected_status
            
            result = get_task_status("test-task-id")
        
        assert result == expected_status
        mock_cache.get.assert_called_once_with("task:test-task-id")

    def test_get_task_status_not_found(self, celery_test_app):
        """Test getting task status when not found."""
        with patch('app.tasks.fetch_tasks.cache') as mock_cache:
            mock_cache.get.return_value = None
            
            result = get_task_status("non-existent-task")
        
        assert result is None


class TestTasksWithDatabase:
    """Test Celery tasks that require database access."""
    
    def test_process_and_store_items_with_database(self, celery_test_app, mock_session_local_for_tasks, sample_hacker_news_items):
        """Test process_and_store_items task with actual database operations."""
        with patch('app.tasks.fetch_tasks.hacker_news_client') as mock_client:
            mock_client.filter_items.return_value = sample_hacker_news_items
            
            # Execute the task
            result = process_and_store_items(sample_hacker_news_items, min_score=50, keyword="AI")
        
        # Verify the result
        assert result["items_processed"] == len(sample_hacker_news_items)
        assert result["items_filtered"] == len(sample_hacker_news_items)
        assert result["items_stored"] > 0
        assert result["filters_applied"]["min_score"] == 50
        assert result["filters_applied"]["keyword"] == "AI"
