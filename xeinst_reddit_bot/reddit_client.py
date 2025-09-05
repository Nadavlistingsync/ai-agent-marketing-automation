"""
Reddit client for Xeinst Reddit Bot
Handles Reddit API interactions using PRAW
"""

import praw
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import time
import random

logger = logging.getLogger(__name__)

class RedditClient:
    """Reddit API client using PRAW"""
    
    def __init__(self, credentials: Dict[str, str]):
        self.reddit = praw.Reddit(
            client_id=credentials['client_id'],
            client_secret=credentials['client_secret'],
            username=credentials['username'],
            password=credentials['password'],
            user_agent=credentials['user_agent']
        )
        
        # Test connection
        try:
            self.reddit.user.me()
            logger.info(f"Reddit client initialized for user: {self.reddit.user.me().name}")
        except Exception as e:
            logger.error(f"Failed to initialize Reddit client: {e}")
            raise
    
    def search_new_posts(self, subreddits: List[str], keywords: List[str], limit: int = 25) -> List[Dict[str, Any]]:
        """Search for new posts matching keywords in target subreddits"""
        matching_posts = []
        
        for subreddit_name in subreddits:
            try:
                subreddit = self.reddit.subreddit(subreddit_name)
                logger.info(f"Searching r/{subreddit_name} for keywords: {keywords}")
                
                # Search for posts with keywords
                for keyword in keywords:
                    try:
                        search_results = subreddit.search(
                            keyword, 
                            sort='new', 
                            time_filter='day', 
                            limit=limit
                        )
                        
                        for post in search_results:
                            # Skip if post is too old (more than 24 hours)
                            if datetime.fromtimestamp(post.created_utc) < datetime.now() - timedelta(days=1):
                                continue
                            
                            # Skip if post is from bot account
                            if post.author.name == self.reddit.user.me().name:
                                continue
                            
                            # Check if post matches multiple keywords
                            matched_keywords = []
                            post_text = f"{post.title} {post.selftext}".lower()
                            
                            for kw in keywords:
                                if kw.lower() in post_text:
                                    matched_keywords.append(kw)
                            
                            if matched_keywords:
                                post_data = {
                                    'id': post.id,
                                    'title': post.title,
                                    'content': post.selftext,
                                    'author': post.author.name,
                                    'karma': post.score,
                                    'created_utc': post.created_utc,
                                    'subreddit': subreddit_name,
                                    'url': f"https://reddit.com{post.permalink}",
                                    'keywords_matched': matched_keywords,
                                    'comment_count': post.num_comments,
                                    'is_self': post.is_self,
                                    'flair': post.link_flair_text
                                }
                                
                                matching_posts.append(post_data)
                                logger.info(f"Found matching post: {post.title[:50]}... in r/{subreddit_name}")
                    
                    except Exception as e:
                        logger.error(f"Error searching for keyword '{keyword}' in r/{subreddit_name}: {e}")
                        continue
                
                # Add small delay to respect rate limits
                time.sleep(random.uniform(1, 3))
                
            except Exception as e:
                logger.error(f"Error accessing subreddit r/{subreddit_name}: {e}")
                continue
        
        # Remove duplicates and sort by relevance (more keywords = higher priority)
        unique_posts = {}
        for post in matching_posts:
            post_id = post['id']
            if post_id not in unique_posts or len(post['keywords_matched']) > len(unique_posts[post_id]['keywords_matched']):
                unique_posts[post_id] = post
        
        # Sort by number of keywords matched and post age
        sorted_posts = sorted(
            unique_posts.values(),
            key=lambda x: (len(x['keywords_matched']), -x['created_utc']),
            reverse=True
        )
        
        logger.info(f"Found {len(sorted_posts)} unique matching posts")
        return sorted_posts
    
    def get_subreddit_rules(self, subreddit_name: str) -> Dict[str, Any]:
        """Fetch subreddit rules and guidelines"""
        try:
            subreddit = self.reddit.subreddit(subreddit_name)
            rules = subreddit.rules
            
            rule_data = {
                'subreddit': subreddit_name,
                'rules': [],
                'description': subreddit.description,
                'public_description': subreddit.public_description,
                'created_utc': subreddit.created_utc,
                'subscribers': subreddit.subscribers,
                'active_user_count': subreddit.active_user_count
            }
            
            for rule in rules:
                rule_data['rules'].append({
                    'kind': rule.kind,
                    'description': rule.description,
                    'short_name': rule.short_name,
                    'violation_reason': rule.violation_reason,
                    'created_utc': rule.created_utc
                })
            
            logger.info(f"Fetched {len(rule_data['rules'])} rules for r/{subreddit_name}")
            return rule_data
            
        except Exception as e:
            logger.error(f"Error fetching rules for r/{subreddit_name}: {e}")
            return {
                'subreddit': subreddit_name,
                'rules': [],
                'error': str(e)
            }
    
    def post_reply(self, post_id: str, reply_text: str, subreddit_name: str) -> Optional[Dict[str, Any]]:
        """Post a reply to a Reddit post"""
        try:
            post = self.reddit.submission(id=post_id)
            
            # Check if post is still accessible
            if not post.title:
                logger.error(f"Post {post_id} is no longer accessible")
                return None
            
            # Check if we've already replied to this post
            for comment in post.comments:
                if comment.author and comment.author.name == self.reddit.user.me().name:
                    logger.warning(f"Already replied to post {post_id}")
                    return None
            
            # Post the reply
            reply = post.reply(reply_text)
            
            # Wait for the reply to be processed
            time.sleep(2)
            
            # Refresh to get the reply details
            reply.refresh()
            
            reply_data = {
                'reply_id': reply.id,
                'post_id': post_id,
                'subreddit': subreddit_name,
                'reply_text': reply_text,
                'posted_at': datetime.now().isoformat(),
                'karma': reply.score,
                'permalink': f"https://reddit.com{reply.permalink}"
            }
            
            logger.info(f"Successfully posted reply to r/{subreddit_name}: {reply.id}")
            return reply_data
            
        except Exception as e:
            logger.error(f"Error posting reply to {post_id}: {e}")
            return None
    
    def reply_to_comment(self, comment_id: str, reply_text: str, subreddit_name: str) -> Optional[Dict[str, Any]]:
        """Reply to a specific comment"""
        try:
            comment = self.reddit.comment(id=comment_id)
            
            # Check if comment is still accessible
            if not comment.body:
                logger.error(f"Comment {comment_id} is no longer accessible")
                return None
            
            # Check if we've already replied to this comment
            for reply in comment.replies:
                if reply.author and reply.author.name == self.reddit.user.me().name:
                    logger.warning(f"Already replied to comment {comment_id}")
                    return None
            
            # Post the reply
            reply = comment.reply(reply_text)
            
            # Wait for the reply to be processed
            time.sleep(2)
            
            # Refresh to get the reply details
            reply.refresh()
            
            reply_data = {
                'reply_id': reply.id,
                'comment_id': comment_id,
                'subreddit': subreddit_name,
                'reply_text': reply_text,
                'posted_at': datetime.now().isoformat(),
                'karma': reply.score,
                'permalink': f"https://reddit.com{reply.permalink}"
            }
            
            logger.info(f"Successfully replied to comment in r/{subreddit_name}: {reply.id}")
            return reply_data
            
        except Exception as e:
            logger.error(f"Error replying to comment {comment_id}: {e}")
            return None
    
    def check_user_karma(self, username: str) -> Dict[str, Any]:
        """Check karma and account age for a user"""
        try:
            user = self.reddit.redditor(username)
            
            # Get user info
            user_info = {
                'username': username,
                'comment_karma': user.comment_karma,
                'link_karma': user.link_karma,
                'total_karma': user.comment_karma + user.link_karma,
                'created_utc': user.created_utc,
                'account_age_days': (datetime.now() - datetime.fromtimestamp(user.created_utc)).days,
                'is_gold': user.is_gold,
                'is_mod': user.is_mod
            }
            
            return user_info
            
        except Exception as e:
            logger.error(f"Error checking karma for user {username}: {e}")
            return {
                'username': username,
                'error': str(e)
            }
    
    def check_post_visibility(self, post_id: str) -> bool:
        """Check if a post is visible (not shadowbanned)"""
        try:
            post = self.reddit.submission(id=post_id)
            
            # Try to access post attributes
            title = post.title
            author = post.author.name if post.author else None
            
            # If we can access these, the post is visible
            return bool(title and author)
            
        except Exception as e:
            logger.error(f"Error checking visibility for post {post_id}: {e}")
            return False
    
    def get_user_posts(self, username: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent posts by a user"""
        try:
            user = self.reddit.redditor(username)
            posts = []
            
            for submission in user.submissions.new(limit=limit):
                post_data = {
                    'id': submission.id,
                    'title': submission.title,
                    'subreddit': submission.subreddit.display_name,
                    'karma': submission.score,
                    'created_utc': submission.created_utc,
                    'url': f"https://reddit.com{submission.permalink}"
                }
                posts.append(post_data)
            
            return posts
            
        except Exception as e:
            logger.error(f"Error getting posts for user {username}: {e}")
            return []
    
    def get_user_comments(self, username: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent comments by a user"""
        try:
            user = self.reddit.redditor(username)
            comments = []
            
            for comment in user.comments.new(limit=limit):
                comment_data = {
                    'id': comment.id,
                    'body': comment.body[:200] + "..." if len(comment.body) > 200 else comment.body,
                    'subreddit': comment.subreddit.display_name,
                    'karma': comment.score,
                    'created_utc': comment.created_utc,
                    'permalink': f"https://reddit.com{comment.permalink}"
                }
                comments.append(comment_data)
            
            return comments
            
        except Exception as e:
            logger.error(f"Error getting comments for user {username}: {e}")
            return []
    
    def check_rate_limit_status(self) -> Dict[str, Any]:
        """Check current rate limit status"""
        try:
            # PRAW handles rate limiting automatically, but we can check the response headers
            # This is a simplified check - in practice, PRAW will throw exceptions when rate limited
            
            status = {
                'status': 'ok',
                'remaining_requests': 'unknown',
                'reset_time': 'unknown',
                'last_request': datetime.now().isoformat()
            }
            
            return status
            
        except Exception as e:
            logger.error(f"Error checking rate limit status: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def test_connection(self) -> bool:
        """Test Reddit API connection"""
        try:
            me = self.reddit.user.me()
            logger.info(f"Reddit connection test successful for user: {me.name}")
            return True
        except Exception as e:
            logger.error(f"Reddit connection test failed: {e}")
            return False
