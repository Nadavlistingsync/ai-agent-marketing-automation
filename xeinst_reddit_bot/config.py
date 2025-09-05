"""
Configuration loader for Xeinst Reddit Bot
Loads environment variables and YAML configuration
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, List
from dotenv import load_dotenv

class Config:
    """Configuration manager for the bot"""
    
    def __init__(self, config_path: str = "config.yaml"):
        # Load environment variables
        load_dotenv()
        
        # Load YAML configuration
        self.config_path = Path(config_path)
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        with open(self.config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        # Validate configuration
        self._validate_config()
    
    def _validate_config(self) -> None:
        """Validate required configuration fields"""
        required_fields = [
            'subreddits', 'keywords', 'content', 'moderation', 
            'rate_limits', 'scheduler', 'logging', 'safety'
        ]
        
        for field in required_fields:
            if field not in self.config:
                raise ValueError(f"Missing required configuration field: {field}")
        
        # Validate subreddits
        for sub in self.config['subreddits']:
            required_sub_fields = ['name', 'subreddit', 'cooldown_hours', 'karma_min']
            for field in required_sub_fields:
                if field not in sub:
                    raise ValueError(f"Missing required field '{field}' in subreddit {sub.get('name', 'unknown')}")
    
    @property
    def reddit_credentials(self) -> Dict[str, str]:
        """Get Reddit API credentials from environment"""
        required_vars = [
            'REDDIT_CLIENT_ID', 'REDDIT_CLIENT_SECRET', 
            'REDDIT_USERNAME', 'REDDIT_PASSWORD', 'REDDIT_USER_AGENT'
        ]
        
        credentials = {}
        for var in required_vars:
            value = os.getenv(var)
            if not value:
                raise ValueError(f"Missing required environment variable: {var}")
            credentials[var.lower().replace('reddit_', '')] = value
        
        return credentials
    
    @property
    def ollama_config(self) -> Dict[str, str]:
        """Get Ollama configuration"""
        return {
            'base_url': os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434'),
            'model': os.getenv('OLLAMA_MODEL', 'llama3')
        }
    
    @property
    def bot_config(self) -> Dict[str, Any]:
        """Get bot configuration with defaults"""
        return {
            'environment': 'production',
            'log_level': os.getenv('LOG_LEVEL', 'INFO'),
            'auto_approve_subs': [],  # No auto-approval by default
            'max_posts_per_day': 10,
            'max_comments_per_day': 50
        }
    
    @property
    def database_path(self) -> str:
        """Get database path"""
        return os.getenv('DATABASE_PATH', 'data/xeinst_bot.db')
    
    @property
    def subreddits(self) -> List[Dict[str, Any]]:
        """Get configured subreddits"""
        return self.config['subreddits']
    
    @property
    def keywords(self) -> List[str]:
        """Get target keywords"""
        return self.config['keywords']
    
    @property
    def content_settings(self) -> Dict[str, Any]:
        """Get content generation settings"""
        return self.config['content']
    
    @property
    def moderation_settings(self) -> Dict[str, Any]:
        """Get moderation settings"""
        return self.config['moderation']
    
    @property
    def rate_limits(self) -> Dict[str, Any]:
        """Get rate limiting configuration"""
        return self.config['rate_limits']
    
    @property
    def scheduler_settings(self) -> Dict[str, Any]:
        """Get scheduler configuration"""
        return self.config['scheduler']
    
    @property
    def logging_settings(self) -> Dict[str, Any]:
        """Get logging configuration"""
        return self.config['logging']
    
    @property
    def safety_settings(self) -> Dict[str, Any]:
        """Get safety configuration"""
        return self.config['safety']
    
    def get_subreddit_config(self, subreddit_name: str) -> Dict[str, Any]:
        """Get configuration for a specific subreddit"""
        for sub in self.subreddits:
            if sub['subreddit'].lower() == subreddit_name.lower():
                return sub
        return None
    
    def is_auto_approve_sub(self, subreddit_name: str) -> bool:
        """Check if a subreddit allows auto-approval"""
        auto_approve_subs = self.bot_config['auto_approve_subs']
        return any(sub.strip() in auto_approve_subs for sub in auto_approve_subs if sub.strip())
    
    def get_posting_hours(self, subreddit_name: str) -> List[int]:
        """Get allowed posting hours for a subreddit"""
        sub_config = self.get_subreddit_config(subreddit_name)
        if sub_config and 'posting_hours' in sub_config:
            return sub_config['posting_hours']
        return list(range(9, 18))  # Default: 9 AM - 6 PM
    
    def get_cooldown_hours(self, subreddit_name: str) -> int:
        """Get cooldown hours for a subreddit"""
        sub_config = self.get_subreddit_config(subreddit_name)
        if sub_config:
            return sub_config['cooldown_hours']
        return 24  # Default: 24 hours
    
    def get_karma_min(self, subreddit_name: str) -> int:
        """Get minimum karma requirement for a subreddit"""
        sub_config = self.get_subreddit_config(subreddit_name)
        if sub_config:
            return sub_config['karma_min']
        return 100  # Default: 100 karma
    
    def allows_links(self, subreddit_name: str) -> bool:
        """Check if a subreddit allows links"""
        sub_config = self.get_subreddit_config(subreddit_name)
        if sub_config:
            return sub_config.get('allow_links', False)
        return False  # Default: no links
    
    def get_content_length_limits(self) -> Dict[str, int]:
        """Get content length limits"""
        return {
            'default': self.content_settings.get('max_length_default', 120),
            'quick': self.content_settings.get('max_length_quick', 60),
            'min': self.content_settings.get('min_length', 20)
        }
    
    def should_include_xeinst(self, context: str) -> bool:
        """Check if Xeinst should be mentioned based on context"""
        if not self.content_settings.get('include_xeinst_only_when_asked', True):
            return False
        
        # Check if context explicitly asks for marketplaces or agents
        xeinst_triggers = [
            'agent marketplace', 'ai agent marketplace', 'workflow tools',
            'automation platform', 'integration marketplace'
        ]
        
        context_lower = context.lower()
        return any(trigger in context_lower for trigger in xeinst_triggers)
    
    def get_xeinst_mention(self) -> str:
        """Get the Xeinst mention text"""
        return self.content_settings.get('xeinst_mention', 
            "If helpful, here's a directory I'm building: Xeinst (ai agent marketplace).")
    
    def get_global_cooldown(self) -> tuple:
        """Get global cooldown range in seconds"""
        min_cooldown = self.rate_limits.get('global_cooldown_min', 90)
        max_cooldown = self.rate_limits.get('global_cooldown_max', 150)
        return (min_cooldown, max_cooldown)
    
    def get_sub_cooldown_hours(self) -> int:
        """Get subreddit cooldown in hours"""
        return self.rate_limits.get('sub_cooldown_hours', 12)
    
    def get_max_posts_per_day(self) -> int:
        """Get maximum posts per day"""
        return self.rate_limits.get('max_posts_per_day', 10)
    
    def get_max_comments_per_day(self) -> int:
        """Get maximum comments per day"""
        return self.rate_limits.get('max_comments_per_day', 50)
    
    def get_max_actions_per_hour(self) -> int:
        """Get maximum actions per hour"""
        return self.rate_limits.get('max_actions_per_hour', 20)
    
    def get_scheduler_intervals(self) -> Dict[str, int]:
        """Get scheduler intervals"""
        return {
            'monitor': self.scheduler_settings.get('monitor_interval_minutes', 15),
            'post': self.scheduler_settings.get('post_interval_minutes', 30),
            'health_check': self.scheduler_settings.get('health_check_interval_hours', 1),
            'daily_report_hour': self.scheduler_settings.get('daily_report_hour', 9)
        }
    
    def get_safety_settings(self) -> Dict[str, Any]:
        """Get safety configuration"""
        return {
            'shadowban_check_interval': self.safety_settings.get('shadowban_check_interval_hours', 6),
            'mod_feedback_threshold': self.safety_settings.get('mod_feedback_threshold', 2),
            'auto_disable_on_negative_mod': self.safety_settings.get('auto_disable_on_negative_mod', True),
            'respect_no_promo_flairs': self.safety_settings.get('respect_no_promo_flairs', True)
        }
    
    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration"""
        return {
            'level': self.logging_settings.get('level', 'INFO'),
            'file': self.logging_settings.get('file', 'logs/xeinst_bot.log'),
            'max_size_mb': self.logging_settings.get('max_size_mb', 10),
            'backup_count': self.logging_settings.get('backup_count', 5)
        }
    
    def get_moderation_config(self) -> Dict[str, Any]:
        """Get moderation configuration"""
        return {
            'toxicity_threshold': self.moderation_settings.get('toxicity_threshold', 0.7),
            'repetition_threshold': self.moderation_settings.get('repetition_threshold', 0.3),
            'blacklisted_words': self.moderation_settings.get('blacklisted_words', [])
        }
