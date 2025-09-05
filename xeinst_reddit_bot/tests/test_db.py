"""
Unit tests for database operations
"""

import pytest
import tempfile
import os
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from db import Database

class TestDatabase:
    """Test database operations"""
    
    def setup_method(self):
        """Set up test database"""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test.db")
        self.database = Database(self.db_path)
    
    def teardown_method(self):
        """Clean up test database"""
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        if os.path.exists(self.temp_dir):
            os.rmdir(self.temp_dir)
    
    def test_database_initialization(self):
        """Test database initialization"""
        assert os.path.exists(self.db_path)
        
        # Check if tables were created
        with self.database.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            expected_tables = ['queue', 'history', 'subreddits', 'keywords', 'rate_limits', 'mod_feedback', 'daily_stats']
            for table in expected_tables:
                assert table in tables
    
    def test_add_to_queue(self):
        """Test adding items to queue"""
        queue_item = {
            'subreddit': 'test',
            'post_id': 'abc123',
            'post_title': 'Test Post',
            'post_content': 'Test content',
            'post_author': 'testuser',
            'post_karma': 10,
            'post_created_utc': 1234567890,
            'keywords_matched': 'test, keyword',
            'draft_reply': 'Test reply',
            'reply_length': 10,
            'includes_xeinst': False
        }
        
        queue_id = self.database.add_to_queue(queue_item)
        assert queue_id > 0
        
        # Verify item was added
        items = self.database.get_queue_items(status='pending')
        assert len(items) == 1
        assert items[0]['post_id'] == 'abc123'
    
    def test_seed_keywords(self):
        """Test seeding keywords"""
        keywords = ['test1', 'test2', 'test3']
        count = self.database.seed_keywords(keywords)
        assert count == 3
        
        # Verify keywords were added
        active_keywords = self.database.get_active_keywords()
        assert len(active_keywords) == 3
        assert 'test1' in active_keywords
    
    def test_rate_limiting(self):
        """Test rate limiting functionality"""
        # Check rate limit
        allowed = self.database.check_rate_limit('test', 'identifier', 1, 60)
        assert allowed is True
        
        # Record action
        success = self.database.record_action('test', 'identifier', 1, 60)
        assert success is True
        
        # Check rate limit again
        allowed = self.database.check_rate_limit('test', 'identifier', 1, 60)
        assert allowed is False
    
    def test_daily_stats(self):
        """Test daily statistics"""
        today = '2024-01-01'
        
        # Create daily stats
        stats_id = self.database.get_or_create_daily_stats(today)
        assert stats_id > 0
        
        # Update stats
        success = self.database.update_daily_stats(today, posts_made=1, comments_made=2)
        assert success is True
    
    def test_cleanup_old_data(self):
        """Test cleanup functionality"""
        # This is a basic test - in practice you'd add old data first
        cleanup_stats = self.database.cleanup_old_data(days=1)
        assert isinstance(cleanup_stats, dict)
        assert 'history_deleted' in cleanup_stats

if __name__ == "__main__":
    pytest.main([__file__])
