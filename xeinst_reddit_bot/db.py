"""
Database operations for Xeinst Reddit Bot
SQLite database with tables for queue, history, subreddits, keywords, and rate limits
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class Database:
    """SQLite database manager for the bot"""
    
    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_database()
    
    def get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable dict-like access
        return conn
    
    def init_database(self):
        """Initialize database schema"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Queue table - stores draft replies waiting for approval
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    subreddit TEXT NOT NULL,
                    post_id TEXT NOT NULL,
                    post_title TEXT NOT NULL,
                    post_content TEXT,
                    post_author TEXT NOT NULL,
                    post_karma INTEGER DEFAULT 0,
                    post_created_utc INTEGER NOT NULL,
                    keywords_matched TEXT NOT NULL,
                    draft_reply TEXT NOT NULL,
                    reply_length INTEGER NOT NULL,
                    includes_xeinst BOOLEAN DEFAULT FALSE,
                    status TEXT DEFAULT 'pending',
                    priority INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # History table - stores all posted replies
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    queue_id INTEGER,
                    subreddit TEXT NOT NULL,
                    post_id TEXT NOT NULL,
                    post_title TEXT NOT NULL,
                    post_author TEXT NOT NULL,
                    reply_id TEXT NOT NULL,
                    reply_content TEXT NOT NULL,
                    reply_karma INTEGER DEFAULT 0,
                    reply_length INTEGER NOT NULL,
                    includes_xeinst BOOLEAN DEFAULT FALSE,
                    posted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    karma_at_post INTEGER DEFAULT 0,
                    current_karma INTEGER DEFAULT 0,
                    last_karma_check TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (queue_id) REFERENCES queue (id)
                )
            """)
            
            # Subreddits table - stores subreddit configurations and status
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS subreddits (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    subreddit TEXT NOT NULL UNIQUE,
                    cooldown_hours INTEGER DEFAULT 24,
                    karma_min INTEGER DEFAULT 100,
                    allow_links BOOLEAN DEFAULT FALSE,
                    posting_hours TEXT NOT NULL,  -- JSON array of hours
                    auto_approve BOOLEAN DEFAULT FALSE,
                    is_active BOOLEAN DEFAULT TRUE,
                    last_post_time TIMESTAMP,
                    last_comment_time TIMESTAMP,
                    posts_today INTEGER DEFAULT 0,
                    comments_today INTEGER DEFAULT 0,
                    mod_feedback_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Keywords table - stores target keywords and their usage
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS keywords (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    keyword TEXT NOT NULL UNIQUE,
                    is_active BOOLEAN DEFAULT TRUE,
                    match_count INTEGER DEFAULT 0,
                    last_matched TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Rate limits table - stores rate limiting information
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS rate_limits (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    type TEXT NOT NULL,  -- 'global', 'subreddit', 'hourly', 'daily'
                    identifier TEXT NOT NULL,  -- 'global', subreddit name, etc.
                    action_count INTEGER DEFAULT 0,
                    window_start TIMESTAMP NOT NULL,
                    window_end TIMESTAMP NOT NULL,
                    max_actions INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Mod feedback table - stores moderator feedback and actions
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS mod_feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    subreddit TEXT NOT NULL,
                    feedback_type TEXT NOT NULL,  -- 'warning', 'removal', 'ban', 'positive'
                    feedback_content TEXT,
                    post_id TEXT,
                    comment_id TEXT,
                    mod_username TEXT,
                    action_taken TEXT,  -- 'none', 'cooldown', 'disable_sub'
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Daily stats table - stores daily activity statistics
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS daily_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE NOT NULL UNIQUE,
                    posts_made INTEGER DEFAULT 0,
                    comments_made INTEGER DEFAULT 0,
                    approvals_given INTEGER DEFAULT 0,
                    drafts_skipped INTEGER DEFAULT 0,
                    karma_gained INTEGER DEFAULT 0,
                    errors_encountered INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for better performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_queue_status ON queue (status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_queue_subreddit ON queue (subreddit)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_history_subreddit ON history (subreddit)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_history_posted_at ON history (posted_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_rate_limits_type_identifier ON rate_limits (type, identifier)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_rate_limits_window ON rate_limits (window_start, window_end)")
            
            conn.commit()
            logger.info("Database initialized successfully")
    
    # Queue operations
    def add_to_queue(self, queue_item: Dict[str, Any]) -> int:
        """Add a new item to the queue"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO queue (
                    subreddit, post_id, post_title, post_content, post_author,
                    post_karma, post_created_utc, keywords_matched, draft_reply,
                    reply_length, includes_xeinst, priority
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                queue_item['subreddit'], queue_item['post_id'], queue_item['post_title'],
                queue_item['post_content'], queue_item['post_author'], queue_item['post_karma'],
                queue_item['post_created_utc'], queue_item['keywords_matched'],
                queue_item['draft_reply'], queue_item['reply_length'],
                queue_item['includes_xeinst'], queue_item.get('priority', 1)
            ))
            
            conn.commit()
            return cursor.lastrowid
    
    def get_queue_items(self, status: str = 'pending') -> List[Dict[str, Any]]:
        """Get queue items by status"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM queue 
                WHERE status = ? 
                ORDER BY priority DESC, created_at ASC
            """, (status,))
            
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def get_recent_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent history items"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM history 
                ORDER BY created_at DESC 
                LIMIT ?
            """, (limit,))
            
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def get_daily_stats(self, date: datetime.date) -> Dict[str, Any]:
        """Get daily statistics for a specific date"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            start_date = datetime.combine(date, datetime.min.time())
            end_date = datetime.combine(date, datetime.max.time())
            
            cursor.execute("""
                SELECT 
                    COUNT(*) as posts_made,
                    SUM(CASE WHEN action_type = 'post' THEN 1 ELSE 0 END) as posts,
                    SUM(CASE WHEN action_type = 'comment' THEN 1 ELSE 0 END) as comments,
                    SUM(karma_gained) as karma_gained
                FROM history 
                WHERE created_at BETWEEN ? AND ?
            """, (start_date, end_date))
            
            row = cursor.fetchone()
            if row:
                return {
                    'posts_made': row[0] or 0,
                    'posts': row[1] or 0,
                    'comments': row[2] or 0,
                    'karma_gained': row[3] or 0
                }
            return {'posts_made': 0, 'posts': 0, 'comments': 0, 'karma_gained': 0}
    
    def delete_queue_item(self, queue_id: int) -> bool:
        """Delete a queue item"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM queue WHERE id = ?", (queue_id,))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error deleting queue item {queue_id}: {e}")
            return False
    
    def update_queue_status(self, queue_id: int, status: str, **kwargs) -> bool:
        """Update queue item status and other fields"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Build dynamic update query
            fields = ['status', 'updated_at'] + list(kwargs.keys())
            placeholders = ', '.join([f"{field} = ?" for field in fields])
            
            values = [status, datetime.now()] + list(kwargs.values()) + [queue_id]
            
            cursor.execute(f"UPDATE queue SET {placeholders} WHERE id = ?", values)
            conn.commit()
            
            return cursor.rowcount > 0
    
    def remove_from_queue(self, queue_id: int) -> bool:
        """Remove item from queue"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM queue WHERE id = ?", (queue_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    # History operations
    def add_to_history(self, history_item: Dict[str, Any]) -> int:
        """Add a posted reply to history"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO history (
                    queue_id, subreddit, post_id, post_title, post_author,
                    reply_id, reply_content, reply_length, includes_xeinst
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                history_item.get('queue_id'), history_item['subreddit'],
                history_item['post_id'], history_item['post_title'],
                history_item['post_author'], history_item['reply_id'],
                history_item['reply_content'], history_item['reply_length'],
                history_item['includes_xeinst']
            ))
            
            conn.commit()
            return cursor.lastrowid
    
    def update_reply_karma(self, reply_id: str, current_karma: int) -> bool:
        """Update karma for a reply"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE history 
                SET current_karma = ?, last_karma_check = CURRENT_TIMESTAMP
                WHERE reply_id = ?
            """, (current_karma, reply_id))
            
            conn.commit()
            return cursor.rowcount > 0
    
    def get_history_stats(self, days: int = 30) -> Dict[str, Any]:
        """Get historical statistics"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            since_date = datetime.now() - timedelta(days=days)
            
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_replies,
                    SUM(reply_karma) as total_karma,
                    AVG(reply_karma) as avg_karma,
                    COUNT(CASE WHEN includes_xeinst THEN 1 END) as xeinst_mentions
                FROM history 
                WHERE posted_at >= ?
            """, (since_date,))
            
            row = cursor.fetchone()
            return dict(row) if row else {}
    
    # Subreddit operations
    def seed_subreddits(self, subreddits: List[Dict[str, Any]]) -> int:
        """Seed subreddits table with initial data"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            count = 0
            for sub in subreddits:
                try:
                    cursor.execute("""
                        INSERT OR REPLACE INTO subreddits (
                            name, subreddit, cooldown_hours, karma_min, allow_links,
                            posting_hours, auto_approve
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        sub['name'], sub['subreddit'], sub['cooldown_hours'],
                        sub['karma_min'], sub['allow_links'],
                        json.dumps(sub['posting_hours']), sub.get('auto_approve', False)
                    ))
                    count += 1
                except Exception as e:
                    logger.error(f"Error seeding subreddit {sub['name']}: {e}")
            
            conn.commit()
            return count
    
    def get_subreddit_config(self, subreddit_name: str) -> Optional[Dict[str, Any]]:
        """Get subreddit configuration"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM subreddits WHERE subreddit = ?", (subreddit_name,))
            row = cursor.fetchone()
            
            if row:
                config = dict(row)
                config['posting_hours'] = json.loads(config['posting_hours'])
                return config
            return None
    
    def update_subreddit_stats(self, subreddit_name: str, **kwargs) -> bool:
        """Update subreddit statistics"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            fields = list(kwargs.keys()) + ['updated_at']
            placeholders = ', '.join([f"{field} = ?" for field in fields])
            
            values = list(kwargs.values()) + [datetime.now(), subreddit_name]
            
            cursor.execute(f"UPDATE subreddits SET {placeholders} WHERE subreddit = ?", values)
            conn.commit()
            
            return cursor.rowcount > 0
    
    def disable_subreddit(self, subreddit_name: str, reason: str = "Mod feedback") -> bool:
        """Disable a subreddit"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE subreddits 
                SET is_active = FALSE, updated_at = CURRENT_TIMESTAMP
                WHERE subreddit = ?
            """, (subreddit_name,))
            
            # Log the action
            cursor.execute("""
                INSERT INTO mod_feedback (
                    subreddit, feedback_type, feedback_content, action_taken
                ) VALUES (?, 'disable', ?, 'disable_sub')
            """, (subreddit_name, reason))
            
            conn.commit()
            return cursor.rowcount > 0
    
    # Keyword operations
    def seed_keywords(self, keywords: List[str]) -> int:
        """Seed keywords table with initial data"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            count = 0
            for keyword in keywords:
                try:
                    cursor.execute("""
                        INSERT OR IGNORE INTO keywords (keyword) VALUES (?)
                    """, (keyword,))
                    if cursor.rowcount > 0:
                        count += 1
                except Exception as e:
                    logger.error(f"Error seeding keyword {keyword}: {e}")
            
            conn.commit()
            return count
    
    def get_active_keywords(self) -> List[str]:
        """Get all active keywords"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT keyword FROM keywords WHERE is_active = TRUE")
            return [row['keyword'] for row in cursor.fetchall()]
    
    def update_keyword_usage(self, keyword: str) -> bool:
        """Update keyword usage statistics"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE keywords 
                SET match_count = match_count + 1, last_matched = CURRENT_TIMESTAMP
                WHERE keyword = ?
            """, (keyword,))
            
            conn.commit()
            return cursor.rowcount > 0
    
    # Rate limiting operations
    def check_rate_limit(self, limit_type: str, identifier: str, max_actions: int, window_minutes: int) -> bool:
        """Check if rate limit allows action"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            window_start = datetime.now() - timedelta(minutes=window_minutes)
            
            cursor.execute("""
                SELECT COUNT(*) as action_count
                FROM rate_limits 
                WHERE type = ? AND identifier = ? 
                AND window_start >= ?
            """, (limit_type, identifier, window_start))
            
            row = cursor.fetchone()
            current_count = row['action_count'] if row else 0
            
            return current_count < max_actions
    
    def record_action(self, limit_type: str, identifier: str, max_actions: int, window_minutes: int) -> bool:
        """Record an action for rate limiting"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            window_start = datetime.now()
            window_end = window_start + timedelta(minutes=window_minutes)
            
            cursor.execute("""
                INSERT INTO rate_limits (
                    type, identifier, action_count, window_start, window_end, max_actions
                ) VALUES (?, ?, 1, ?, ?, ?)
            """, (limit_type, identifier, window_start, window_end, max_actions))
            
            conn.commit()
            return True
    
    def cleanup_expired_rate_limits(self) -> int:
        """Clean up expired rate limit records"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM rate_limits WHERE window_end < CURRENT_TIMESTAMP")
            deleted_count = cursor.rowcount
            
            conn.commit()
            return deleted_count
    
    # Daily stats operations
    def get_or_create_daily_stats(self, date: str) -> int:
        """Get or create daily stats record"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT id FROM daily_stats WHERE date = ?", (date,))
            row = cursor.fetchone()
            
            if row:
                return row['id']
            else:
                cursor.execute("""
                    INSERT INTO daily_stats (date) VALUES (?)
                """, (date,))
                conn.commit()
                return cursor.lastrowid
    
    def update_daily_stats(self, date: str, **kwargs) -> bool:
        """Update daily statistics"""
        stats_id = self.get_or_create_daily_stats(date)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            fields = list(kwargs.keys())
            placeholders = ', '.join([f"{field} = {field} + ?" for field in fields])
            
            values = list(kwargs.values()) + [stats_id]
            
            cursor.execute(f"UPDATE daily_stats SET {placeholders} WHERE id = ?", values)
            conn.commit()
            
            return cursor.rowcount > 0
    
    # Mod feedback operations
    def add_mod_feedback(self, feedback: Dict[str, Any]) -> int:
        """Add moderator feedback"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO mod_feedback (
                    subreddit, feedback_type, feedback_content, post_id,
                    comment_id, mod_username, action_taken
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                feedback['subreddit'], feedback['feedback_type'],
                feedback.get('feedback_content'), feedback.get('post_id'),
                feedback.get('comment_id'), feedback.get('mod_username'),
                feedback.get('action_taken', 'none')
            ))
            
            conn.commit()
            return cursor.lastrowid
    
    def get_mod_feedback_count(self, subreddit_name: str, days: int = 30) -> int:
        """Get count of negative mod feedback for a subreddit"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            since_date = datetime.now() - timedelta(days=days)
            
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM mod_feedback 
                WHERE subreddit = ? 
                AND feedback_type IN ('warning', 'removal', 'ban')
                AND created_at >= ?
            """, (subreddit_name, since_date))
            
            row = cursor.fetchone()
            return row['count'] if row else 0
    
    # Utility operations
    def get_database_stats(self) -> Dict[str, Any]:
        """Get overall database statistics"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            stats = {}
            
            # Count records in each table
            tables = ['queue', 'history', 'subreddits', 'keywords', 'rate_limits', 'mod_feedback', 'daily_stats']
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
                row = cursor.fetchone()
                stats[f"{table}_count"] = row['count'] if row else 0
            
            # Get recent activity
            cursor.execute("""
                SELECT COUNT(*) as count FROM queue WHERE status = 'pending'
            """)
            row = cursor.fetchone()
            stats['pending_queue_count'] = row['count'] if row else 0
            
            cursor.execute("""
                SELECT COUNT(*) as count FROM history 
                WHERE posted_at >= datetime('now', '-24 hours')
            """)
            row = cursor.fetchone()
            stats['posts_last_24h'] = row['count'] if row else 0
            
            return stats
    
    def cleanup_old_data(self, days: int = 90) -> Dict[str, int]:
        """Clean up old data"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cleanup_date = datetime.now() - timedelta(days=days)
            cleanup_stats = {}
            
            # Clean up old history records
            cursor.execute("DELETE FROM history WHERE posted_at < ?", (cleanup_date,))
            cleanup_stats['history_deleted'] = cursor.rowcount
            
            # Clean up old mod feedback
            cursor.execute("DELETE FROM mod_feedback WHERE created_at < ?", (cleanup_date,))
            cleanup_stats['mod_feedback_deleted'] = cursor.rowcount
            
            # Clean up old daily stats
            cursor.execute("DELETE FROM daily_stats WHERE date < ?", (cleanup_date.strftime('%Y-%m-%d'),))
            cleanup_stats['daily_stats_deleted'] = cursor.rowcount
            
            conn.commit()
            return cleanup_stats
