#!/usr/bin/env python3
"""
Moderation Worker for Xeinst Multi-Channel Poster
Processes approved posts and handles platform posting
"""

import os
import time
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv
import sqlite3

# Load environment variables
load_dotenv()

# Configuration
DB_PATH = os.getenv('DATABASE_PATH', 'xeinst_reddit_bot/data/xeinst_bot.db')
WORKER_INTERVAL = int(os.getenv('WORKER_INTERVAL_SECONDS', '60'))
QUIET_HOURS = os.getenv('QUIET_HOURS', '23-6')
GLOBAL_MAX_POSTS_PER_HOUR = int(os.getenv('GLOBAL_MAX_POSTS_PER_HOUR', '10'))
MAX_POSTS_PER_ACCOUNT_PER_DAY = int(os.getenv('MAX_POSTS_PER_ACCOUNT_PER_DAY', '5'))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/moderation_worker.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ModerationWorker:
    """Worker that processes approved posts"""
    
    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.running = False
    
    def get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def check_kill_switch(self) -> bool:
        """Check if kill switch is enabled"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE key = 'kill_switch'")
            row = cursor.fetchone()
            return row and row['value'] == 'true'
    
    def check_quiet_hours(self) -> bool:
        """Check if we're in quiet hours"""
        current_hour = datetime.now().hour
        quiet_start, quiet_end = map(int, QUIET_HOURS.split('-'))
        return quiet_start <= current_hour or current_hour < quiet_end
    
    def check_rate_limits(self) -> bool:
        """Check if we can post more"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Check hourly limit
            cursor.execute("""
                SELECT COUNT(*) as count FROM posts 
                WHERE status = 'posted' AND created_at >= datetime('now', '-1 hour')
            """)
            hourly_count = cursor.fetchone()['count']
            
            if hourly_count >= GLOBAL_MAX_POSTS_PER_HOUR:
                logger.info(f"Hourly rate limit reached: {hourly_count}/{GLOBAL_MAX_POSTS_PER_HOUR}")
                return False
            
            return True
    
    def get_approved_posts(self) -> list:
        """Get posts ready for posting"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT p.*, a.handle as account_handle 
                FROM posts p 
                JOIN accounts a ON p.account_id = a.id 
                WHERE p.status = 'approved' 
                AND (p.scheduled_at IS NULL OR p.scheduled_at <= datetime('now'))
                ORDER BY p.created_at ASC
            """)
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def post_to_platform(self, post: dict) -> bool:
        """Post content to the specified platform"""
        platform = post['platform']
        title = post['title']
        body = post['body']
        media_path = post['media_path']
        
        logger.info(f"Posting to {platform}: {title[:50]}...")
        
        try:
            # Here you would integrate with your actual platform APIs
            # For now, we'll simulate posting
            
            if platform == 'reddit':
                success = self.post_to_reddit(title, body, media_path)
            elif platform == 'twitter':
                success = self.post_to_twitter(body, media_path)
            elif platform == 'linkedin':
                success = self.post_to_linkedin(title, body, media_path)
            elif platform == 'bluesky':
                success = self.post_to_bluesky(body, media_path)
            else:
                logger.warning(f"Unknown platform: {platform}")
                return False
            
            if success:
                logger.info(f"Successfully posted to {platform}")
                return True
            else:
                logger.error(f"Failed to post to {platform}")
                return False
                
        except Exception as e:
            logger.error(f"Error posting to {platform}: {e}")
            return False
    
    def post_to_reddit(self, title: str, body: str, media_path: str = None) -> bool:
        """Post to Reddit using the existing Reddit bot"""
        try:
            # Import the existing Reddit client
            import sys
            sys.path.append('xeinst_reddit_bot')
            
            from xeinst_reddit_bot.reddit_client import RedditClient
            from xeinst_reddit_bot.config import Config
            
            # Initialize Reddit client
            config = Config()
            reddit_client = RedditClient()
            
            # Determine target subreddit (you might want to make this configurable)
            target_subreddit = "entrepreneur"  # Default subreddit
            
            # Post to Reddit
            logger.info(f"Posting to r/{target_subreddit}: {title}")
            
            # Use the existing Reddit client to post
            success = reddit_client.post_submission(
                subreddit=target_subreddit,
                title=title,
                text=body
            )
            
            if success:
                logger.info(f"Successfully posted to r/{target_subreddit}")
                return True
            else:
                logger.error(f"Failed to post to r/{target_subreddit}")
                return False
                
        except Exception as e:
            logger.error(f"Error posting to Reddit: {e}")
            return False
    
    def post_to_twitter(self, body: str, media_path: str = None) -> bool:
        """Post to Twitter/X"""
        logger.info(f"Would post to Twitter: {body[:100]}...")
        # For now, simulate success
        return True
    
    def post_to_linkedin(self, title: str, body: str, media_path: str = None) -> bool:
        """Post to LinkedIn"""
        logger.info(f"Would post to LinkedIn: {title}")
        # For now, simulate success
        return True
    
    def post_to_bluesky(self, body: str, media_path: str = None) -> bool:
        """Post to Bluesky"""
        try:
            # Import Bluesky client
            from bluesky_client import BlueskyClient
            
            # Initialize Bluesky client
            bluesky_client = BlueskyClient()
            
            # Test connection first
            if not bluesky_client.test_connection():
                logger.warning("Bluesky connection test failed")
                return False
            
            # Post content
            if media_path:
                result = bluesky_client.post_with_media(body, media_path)
            else:
                result = bluesky_client.post_text(body)
            
            if result.get("success"):
                logger.info(f"Successfully posted to Bluesky: {result.get('uri')}")
                return True
            else:
                logger.error(f"Failed to post to Bluesky: {result.get('error')}")
                return False
            
        except Exception as e:
            logger.error(f"Error posting to Bluesky: {e}")
            return False
    
    def update_post_status(self, post_id: int, status: str, external_uri: str = None) -> bool:
        """Update post status after posting"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            update_data = {
                'status': status,
                'updated_at': datetime.now().isoformat()
            }
            
            if external_uri:
                update_data['external_uri'] = external_uri
            
            fields = list(update_data.keys())
            placeholders = ', '.join([f"{field} = ?" for field in fields])
            
            values = list(update_data.values()) + [post_id]
            
            cursor.execute(f"UPDATE posts SET {placeholders} WHERE id = ?", values)
            conn.commit()
            
            return cursor.rowcount > 0
    
    def log_action(self, level: str, message: str, meta: dict = None) -> int:
        """Log an action"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            meta_json = json.dumps(meta) if meta else None
            
            cursor.execute("""
                INSERT INTO logs (level, message, meta_json)
                VALUES (?, ?, ?)
            """, (level, message, meta_json))
            
            conn.commit()
            return cursor.lastrowid
    
    def process_posts(self):
        """Process approved posts"""
        try:
            # Check if we should process posts
            if self.check_kill_switch():
                logger.info("Kill switch is enabled, skipping post processing")
                return
            
            if self.check_quiet_hours():
                logger.info("In quiet hours, skipping post processing")
                return
            
            if not self.check_rate_limits():
                logger.info("Rate limit reached, skipping post processing")
                return
            
            # Get approved posts ready for posting
            approved_posts = self.get_approved_posts()
            
            if not approved_posts:
                logger.info("No approved posts ready for posting")
                return
            
            logger.info(f"Found {len(approved_posts)} approved posts ready for posting")
            
            # Process each post
            for post in approved_posts:
                try:
                    # Check if we can still post (rate limits might change)
                    if not self.check_rate_limits():
                        logger.info("Rate limit reached during processing, stopping")
                        break
                    
                    # Attempt to post
                    success = self.post_to_platform(post)
                    
                    if success:
                        # Update post status to posted
                        external_uri = f"https://{post['platform']}.com/post/{post['id']}"  # Placeholder
                        self.update_post_status(post['post_id'], 'posted', external_uri)
                        
                        # Log success
                        self.log_action('INFO', f"Post {post['post_id']} successfully posted to {post['platform']}", {
                            'post_id': post['post_id'],
                            'platform': post['platform'],
                            'external_uri': external_uri
                        })
                        
                        logger.info(f"Successfully posted {post['post_id']} to {post['platform']}")
                    else:
                        # Update post status to failed
                        self.update_post_status(post['post_id'], 'failed')
                        
                        # Log failure
                        self.log_action('ERROR', f"Post {post['post_id']} failed to post to {post['platform']}", {
                            'post_id': post['post_id'],
                            'platform': post['platform']
                        })
                        
                        logger.error(f"Failed to post {post['post_id']} to {post['platform']}")
                
                except Exception as e:
                    logger.error(f"Error processing post {post['post_id']}: {e}")
                    
                    # Mark as failed
                    self.update_post_status(post['post_id'], 'failed')
                    
                    # Log error
                    self.log_action('ERROR', f"Error processing post {post['post_id']}: {str(e)}", {
                        'post_id': post['post_id'],
                        'error': str(e)
                    })
        
        except Exception as e:
            logger.error(f"Error in process_posts: {e}")
            self.log_action('ERROR', f"Worker error: {str(e)}", {'error': str(e)})
    
    def run(self):
        """Run the worker loop"""
        logger.info("Starting moderation worker...")
        self.running = True
        
        while self.running:
            try:
                self.process_posts()
                time.sleep(WORKER_INTERVAL)
            except KeyboardInterrupt:
                logger.info("Worker interrupted, shutting down...")
                self.running = False
            except Exception as e:
                logger.error(f"Unexpected error in worker loop: {e}")
                time.sleep(WORKER_INTERVAL)
        
        logger.info("Worker stopped")

def main():
    """Main entry point"""
    # Ensure logs directory exists
    Path('logs').mkdir(exist_ok=True)
    
    # Create and run worker
    worker = ModerationWorker(DB_PATH)
    
    try:
        worker.run()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise

if __name__ == "__main__":
    main()
