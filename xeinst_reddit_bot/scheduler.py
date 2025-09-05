"""
Task scheduler for Xeinst Reddit Bot
Handles automated monitoring, posting, and health checks
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
import time
import random

logger = logging.getLogger(__name__)

class BotScheduler:
    """Scheduler for automated bot tasks"""
    
    def __init__(self, config: Dict[str, Any], database, reddit_client, llm_client, moderator):
        self.config = config
        self.database = database
        self.reddit_client = reddit_client
        self.llm_client = llm_client
        self.moderator = moderator
        
        # Initialize scheduler
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()
        
        # Get scheduling configuration
        self.scheduler_config = config.get('scheduler', {})
        self.monitor_interval = self.scheduler_config.get('monitor_interval_minutes', 15)
        self.post_interval = self.scheduler_config.get('post_interval_minutes', 30)
        self.health_check_interval = self.scheduler_config.get('health_check_interval_hours', 1)
        self.daily_report_hour = self.scheduler_config.get('daily_report_hour', 9)
        
        # Schedule jobs
        self._schedule_jobs()
        
        logger.info("Bot scheduler initialized and started")
    
    def _schedule_jobs(self):
        """Schedule all automated jobs"""
        
        # Monitor keywords and enqueue drafts
        self.scheduler.add_job(
            func=self._monitor_keywords_job,
            trigger=IntervalTrigger(minutes=self.monitor_interval),
            id='monitor_keywords',
            name='Monitor keywords and enqueue drafts',
            max_instances=1,
            coalesce=True
        )
        
        # Post scheduler for approved items
        self.scheduler.add_job(
            func=self._post_scheduler_job,
            trigger=IntervalTrigger(minutes=self.post_interval),
            id='post_scheduler',
            name='Post approved content',
            max_instances=1,
            coalesce=True
        )
        
        # Health checks
        self.scheduler.add_job(
            func=self._health_check_job,
            trigger=IntervalTrigger(hours=self.health_check_interval),
            id='health_check',
            name='System health check',
            max_instances=1,
            coalesce=True
        )
        
        # Daily report
        self.scheduler.add_job(
            func=self._daily_report_job,
            trigger=CronTrigger(hour=self.daily_report_hour, minute=0),
            id='daily_report',
            name='Daily activity report',
            max_instances=1,
            coalesce=True
        )
        
        # Shadowban check
        shadowban_interval = self.config.get('safety', {}).get('shadowban_check_interval_hours', 6)
        self.scheduler.add_job(
            func=self._shadowban_check_job,
            trigger=IntervalTrigger(hours=shadowban_interval),
            id='shadowban_check',
            name='Shadowban detection check',
            max_instances=1,
            coalesce=True
        )
        
        # Database cleanup
        self.scheduler.add_job(
            func=self._database_cleanup_job,
            trigger=CronTrigger(hour=2, minute=0),  # 2 AM
            id='database_cleanup',
            name='Database cleanup and maintenance',
            max_instances=1,
            coalesce=True
        )
        
        logger.info(f"Scheduled {len(self.scheduler.get_jobs())} jobs")
    
    def _monitor_keywords_job(self):
        """Monitor keywords and create draft replies"""
        try:
            logger.info("Starting keyword monitoring job")
            
            # Get active subreddits and keywords
            subreddits = [sub['subreddit'] for sub in self.config.get('subreddits', []) if sub.get('is_active', True)]
            keywords = self.config.get('keywords', [])
            
            if not subreddits or not keywords:
                logger.warning("No active subreddits or keywords configured")
                return
            
            # Search for new posts
            matching_posts = self.reddit_client.search_new_posts(subreddits, keywords, limit=25)
            
            if not matching_posts:
                logger.info("No new matching posts found")
                return
            
            # Process each matching post
            for post in matching_posts:
                try:
                    self._process_matching_post(post)
                    # Add delay between processing posts
                    time.sleep(random.uniform(2, 5))
                    
                except Exception as e:
                    logger.error(f"Error processing post {post['id']}: {e}")
                    continue
            
            logger.info(f"Keyword monitoring completed. Processed {len(matching_posts)} posts")
            
        except Exception as e:
            logger.error(f"Error in keyword monitoring job: {e}")
    
    def _process_matching_post(self, post: Dict[str, Any]):
        """Process a single matching post and create draft reply"""
        try:
            # Check if we've already processed this post
            existing_queue = self.database.get_queue_items(status='pending', limit=100)
            if any(item['post_id'] == post['id'] for item in existing_queue):
                logger.info(f"Post {post['id']} already in queue, skipping")
                return
            
            # Check if we've already replied to this post
            existing_history = self.database.get_history_stats(days=7)
            # This is a simplified check - in practice you'd query by post_id
            
            # Determine content type based on keywords and post content
            content_type = self._determine_content_type(post)
            
            # Generate draft reply
            draft_result = self._generate_draft_reply(post, content_type)
            
            if not draft_result['success']:
                logger.warning(f"Failed to generate draft for post {post['id']}: {draft_result.get('error')}")
                return
            
            # Check compliance
            compliance_result = self.moderator.check_content_compliance(
                draft_result['content'],
                post['subreddit'],
                post,
                self.config
            )
            
            # Create queue item
            queue_item = {
                'subreddit': post['subreddit'],
                'post_id': post['id'],
                'post_title': post['title'],
                'post_content': post['content'],
                'post_author': post['author'],
                'post_karma': post['karma'],
                'post_created_utc': post['created_utc'],
                'keywords_matched': ', '.join(post['keywords_matched']),
                'draft_reply': draft_result['content'],
                'reply_length': draft_result['length'],
                'includes_xeinst': draft_result['includes_xeinst'],
                'priority': len(post['keywords_matched'])  # More keywords = higher priority
            }
            
            # Add to queue
            queue_id = self.database.add_to_queue(queue_item)
            logger.info(f"Added post {post['id']} to queue with ID {queue_id}")
            
            # Update keyword usage statistics
            for keyword in post['keywords_matched']:
                self.database.update_keyword_usage(keyword)
            
        except Exception as e:
            logger.error(f"Error processing matching post {post['id']}: {e}")
    
    def _determine_content_type(self, post: Dict[str, Any]) -> str:
        """Determine the type of content to generate based on post and keywords"""
        post_text = f"{post['title']} {post['content']}".lower()
        
        # Check for buyer intent
        buyer_keywords = ['looking for', 'need', 'want', 'recommend', 'suggest', 'help']
        if any(keyword in post_text for keyword in buyer_keywords):
            return 'buyer'
        
        # Check for seller intent
        seller_keywords = ['selling', 'created', 'built', 'developed', 'launching', 'marketing']
        if any(keyword in post_text for keyword in seller_keywords):
            return 'seller'
        
        # Check for promoter intent
        promoter_keywords = ['promote', 'affiliate', 'commission', 'referral', 'marketing']
        if any(keyword in post_text for keyword in promoter_keywords):
            return 'promoter'
        
        # Default to general content
        return 'general'
    
    def _generate_draft_reply(self, post: Dict[str, Any], content_type: str) -> Dict[str, Any]:
        """Generate a draft reply using the LLM"""
        try:
            # Determine if Xeinst should be included
            should_include_xeinst = self.config.should_include_xeinst(
                f"{post['title']} {post['content']}"
            )
            
            # Generate content based on type
            if content_type == 'buyer':
                result = self.llm_client.generate_buyer_content(
                    post['content'], post['subreddit'], post['keywords_matched']
                )
            elif content_type == 'seller':
                result = self.llm_client.generate_seller_content(
                    post['content'], post['subreddit'], post['keywords_matched']
                )
            elif content_type == 'promoter':
                result = self.llm_client.generate_promoter_content(
                    post['content'], post['subreddit'], post['keywords_matched']
                )
            else:
                result = self.llm_client.generate_content(
                    "General helpful response",
                    post['content'],
                    post['subreddit'],
                    post['keywords_matched'],
                    include_xeinst=should_include_xeinst
                )
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating draft reply: {e}")
            return {
                'success': False,
                'error': str(e),
                'content': None
            }
    
    def _post_scheduler_job(self):
        """Post approved content from the queue"""
        try:
            logger.info("Starting post scheduler job")
            
            # Get approved items from queue
            approved_items = self.database.get_queue_items(status='approved', limit=10)
            
            if not approved_items:
                logger.info("No approved items to post")
                return
            
            # Process each approved item
            for item in approved_items:
                try:
                    # Check rate limits
                    rate_limit_check = self.moderator.check_rate_limits(
                        item['subreddit'], 'post', self.database
                    )
                    
                    if not rate_limit_check['allowed']:
                        logger.info(f"Rate limited for r/{item['subreddit']}: {rate_limit_check['reason']}")
                        continue
                    
                    # Check if it's within posting hours
                    if not self._is_within_posting_hours(item['subreddit']):
                        logger.info(f"Outside posting hours for r/{item['subreddit']}")
                        continue
                    
                    # Post the reply
                    reply_result = self.reddit_client.post_reply(
                        item['post_id'],
                        item['draft_reply'],
                        item['subreddit']
                    )
                    
                    if reply_result:
                        # Add to history
                        history_item = {
                            'queue_id': item['id'],
                            'subreddit': item['subreddit'],
                            'post_id': item['post_id'],
                            'post_title': item['post_title'],
                            'post_author': item['post_author'],
                            'reply_id': reply_result['reply_id'],
                            'reply_content': item['draft_reply'],
                            'reply_length': item['reply_length'],
                            'includes_xeinst': item['includes_xeinst']
                        }
                        
                        self.database.add_to_history(history_item)
                        
                        # Update queue status
                        self.database.update_queue_status(item['id'], 'posted')
                        
                        # Update subreddit statistics
                        self.database.update_subreddit_stats(
                            item['subreddit'],
                            last_post_time=datetime.now(),
                            posts_today=1
                        )
                        
                        # Record rate limit action
                        self.database.record_action('global', 'global', 1, 90)
                        self.database.record_action('subreddit', item['subreddit'], 1, 12 * 60)
                        
                        # Update daily stats
                        today = datetime.now().strftime('%Y-%m-%d')
                        self.database.update_daily_stats(today, posts_made=1)
                        
                        logger.info(f"Successfully posted reply to r/{item['subreddit']}: {reply_result['reply_id']}")
                        
                        # Add delay between posts
                        time.sleep(random.uniform(90, 150))
                        
                    else:
                        logger.error(f"Failed to post reply for queue item {item['id']}")
                        # Mark as failed
                        self.database.update_queue_status(item['id'], 'failed')
                
                except Exception as e:
                    logger.error(f"Error processing approved item {item['id']}: {e}")
                    # Mark as failed
                    self.database.update_queue_status(item['id'], 'failed')
                    continue
            
            logger.info("Post scheduler job completed")
            
        except Exception as e:
            logger.error(f"Error in post scheduler job: {e}")
    
    def _is_within_posting_hours(self, subreddit: str) -> bool:
        """Check if current time is within posting hours for a subreddit"""
        try:
            sub_config = self.config.get_subreddit_config(subreddit)
            if not sub_config or 'posting_hours' not in sub_config:
                return True  # Default to allowing if no hours specified
            
            current_hour = datetime.now().hour
            posting_hours = sub_config['posting_hours']
            
            return current_hour in posting_hours
            
        except Exception as e:
            logger.error(f"Error checking posting hours for r/{subreddit}: {e}")
            return True  # Default to allowing
    
    def _health_check_job(self):
        """Perform system health checks"""
        try:
            logger.info("Starting health check job")
            
            # Check Reddit API
            reddit_health = self.reddit_client.test_connection()
            
            # Check Ollama
            ollama_health = self.llm_client.health_check()
            
            # Check database
            db_stats = self.database.get_database_stats()
            
            # Log health status
            health_status = {
                'reddit': reddit_health,
                'ollama': ollama_health,
                'database': db_stats,
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"Health check completed: Reddit={reddit_health}, Ollama={ollama_health['status']}")
            
            # If any service is unhealthy, log warning
            if not reddit_health or ollama_health['status'] != 'healthy':
                logger.warning("Some services are unhealthy - check logs for details")
            
        except Exception as e:
            logger.error(f"Error in health check job: {e}")
    
    def _daily_report_job(self):
        """Generate and log daily activity report"""
        try:
            logger.info("Starting daily report job")
            
            yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            
            # Get daily stats
            daily_stats = self.database.get_daily_stats(yesterday)
            
            # Get historical stats
            history_stats = self.database.get_history_stats(days=7)
            
            # Generate report
            report = {
                'date': yesterday,
                'posts_made': daily_stats.get('posts_made', 0),
                'comments_made': daily_stats.get('comments_made', 0),
                'approvals_given': daily_stats.get('approvals_given', 0),
                'drafts_skipped': daily_stats.get('drafts_skipped', 0),
                'karma_gained': daily_stats.get('karma_gained', 0),
                'errors_encountered': daily_stats.get('errors_encountered', 0),
                'weekly_total_replies': history_stats.get('total_replies', 0),
                'weekly_avg_karma': history_stats.get('avg_karma', 0),
                'xeinst_mentions': history_stats.get('xeinst_mentions', 0)
            }
            
            # Log the report
            logger.info(f"Daily Report for {yesterday}: {report}")
            
            # Reset daily counters
            today = datetime.now().strftime('%Y-%m-%d')
            self.database.get_or_create_daily_stats(today)
            
        except Exception as e:
            logger.error(f"Error in daily report job: {e}")
    
    def _shadowban_check_job(self):
        """Check for potential shadowban by monitoring recent posts"""
        try:
            logger.info("Starting shadowban check job")
            
            # Get recent posts from history
            # This is a simplified check - in practice you'd check actual visibility
            
            # For now, just log that the check was performed
            logger.info("Shadowban check completed (simplified implementation)")
            
        except Exception as e:
            logger.error(f"Error in shadowban check job: {e}")
    
    def _database_cleanup_job(self):
        """Clean up old data and perform maintenance"""
        try:
            logger.info("Starting database cleanup job")
            
            # Clean up old rate limit records
            expired_count = self.database.cleanup_expired_rate_limits()
            
            # Clean up old data (older than 90 days)
            cleanup_stats = self.database.cleanup_old_data(days=90)
            
            logger.info(f"Database cleanup completed: {expired_count} expired rate limits, "
                       f"{cleanup_stats.get('history_deleted', 0)} old records removed")
            
        except Exception as e:
            logger.error(f"Error in database cleanup job: {e}")
    
    def get_scheduler_status(self) -> Dict[str, Any]:
        """Get current scheduler status"""
        jobs = self.scheduler.get_jobs()
        
        status = {
            'running': self.scheduler.running,
            'job_count': len(jobs),
            'jobs': []
        }
        
        for job in jobs:
            status['jobs'].append({
                'id': job.id,
                'name': job.name,
                'next_run': job.next_run_time.isoformat() if job.next_run_time else None,
                'trigger': str(job.trigger)
            })
        
        return status
    
    def pause_scheduler(self):
        """Pause the scheduler"""
        self.scheduler.pause()
        logger.info("Scheduler paused")
    
    def resume_scheduler(self):
        """Resume the scheduler"""
        self.scheduler.resume()
        logger.info("Scheduler resumed")
    
    def shutdown(self):
        """Shutdown the scheduler"""
        self.scheduler.shutdown()
        logger.info("Scheduler shutdown")
    
    def add_custom_job(self, func, trigger, **kwargs):
        """Add a custom job to the scheduler"""
        try:
            job = self.scheduler.add_job(func, trigger, **kwargs)
            logger.info(f"Added custom job: {job.id}")
            return job
        except Exception as e:
            logger.error(f"Error adding custom job: {e}")
            return None

# Main execution block
if __name__ == "__main__":
    import sys
    from pathlib import Path
    
    # Add current directory to path
    sys.path.insert(0, str(Path(__file__).parent))
    
    # Import required modules
    from config import Config
    from db import Database
    from reddit_client import RedditClient
    from llm import OllamaClient
    from moderation import ContentModerator
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/xeinst_bot.log'),
            logging.StreamHandler()
        ]
    )
    
    try:
        # Initialize components
        logger.info("Initializing Xeinst Reddit Bot...")
        
        config = Config()
        database = Database(config.database_path)
        reddit_client = RedditClient(config.reddit_credentials)
        llm_client = OllamaClient(config.ollama_config['base_url'], config.ollama_config['model'])
        moderator = ContentModerator(config.config)
        
        # Create and start scheduler
        scheduler = BotScheduler(config.config, database, reddit_client, llm_client, moderator)
        
        logger.info("Bot started successfully! Press Ctrl+C to stop.")
        
        # Keep the main thread alive
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Shutting down bot...")
            scheduler.shutdown()
            logger.info("Bot shutdown complete.")
        
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        sys.exit(1)
