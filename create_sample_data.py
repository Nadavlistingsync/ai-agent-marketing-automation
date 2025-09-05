#!/usr/bin/env python3
"""
Create sample data for the moderation system without requiring full Reddit setup
"""

import os
import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path

def create_sample_data():
    """Create sample posts for testing the moderation system"""
    
    # Database path
    db_path = os.getenv('DATABASE_PATH', 'xeinst_reddit_bot/data/xeinst_bot.db')
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        # Create tables if they don't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                platform TEXT NOT NULL,
                account_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                body TEXT NOT NULL,
                media_path TEXT,
                status TEXT DEFAULT 'draft',
                scheduled_at TIMESTAMP,
                external_uri TEXT,
                similarity_score REAL,
                policy_flags TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                platform TEXT NOT NULL,
                handle TEXT NOT NULL,
                enabled BOOLEAN DEFAULT TRUE,
                last_post_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id INTEGER NOT NULL,
                reviewer TEXT NOT NULL,
                action TEXT NOT NULL,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (post_id) REFERENCES posts (id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT NOT NULL UNIQUE,
                value TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                level TEXT NOT NULL,
                message TEXT NOT NULL,
                meta_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Ensure we have default accounts for Reddit and Bluesky
        cursor.execute("""
            INSERT OR IGNORE INTO accounts (id, platform, handle, enabled)
            VALUES 
            (1, 'reddit', 'xeinst_bot', TRUE),
            (2, 'bluesky', 'xeinst.bsky.social', TRUE)
        """)
        
        # Initialize default settings
        cursor.execute("""
            INSERT OR IGNORE INTO settings (key, value) VALUES 
            ('kill_switch', 'false'),
            ('global_max_posts_per_hour', '10'),
            ('max_posts_per_account_per_day', '5'),
            ('similarity_block_threshold', '0.8')
        """)
        
        # Sample posts data for Reddit and Bluesky
        sample_posts = [
            {
                'platform': 'reddit',
                'account_id': 1,
                'title': 'Automation Tips for Small Businesses',
                'body': 'Here are some great automation tools that can help small businesses save time and money. Xeinst is particularly useful for workflow automation and can integrate with hundreds of apps.',
                'status': 'draft',
                'similarity_score': 0.1,
                'policy_flags': '[]'
            },
            {
                'platform': 'bluesky',
                'account_id': 2,
                'title': 'Building a SaaS Product from Scratch',
                'body': 'Starting a SaaS business requires careful planning and execution. Focus on solving real problems for your target market. Consider using automation tools to streamline your operations.',
                'status': 'draft',
                'similarity_score': 0.2,
                'policy_flags': '[]'
            },
            {
                'platform': 'reddit',
                'account_id': 1,
                'title': 'No-Code Development Trends 2024',
                'body': 'No-code platforms are revolutionizing how we build software. They make development accessible to non-technical founders and can significantly reduce time-to-market.',
                'status': 'draft',
                'similarity_score': 0.15,
                'policy_flags': '[]'
            },
            {
                'platform': 'bluesky',
                'account_id': 2,
                'title': 'Marketing Automation Strategies',
                'body': 'Effective marketing automation can significantly improve your conversion rates and customer engagement. Start with email marketing and gradually expand to other channels.',
                'status': 'draft',
                'similarity_score': 0.3,
                'policy_flags': '[]'
            },
            {
                'platform': 'reddit',
                'account_id': 1,
                'title': 'Workflow Optimization for Remote Teams',
                'body': 'Remote work requires different approaches to workflow management. Use tools like Xeinst to automate repetitive tasks and keep your team focused on high-value work.',
                'status': 'draft',
                'similarity_score': 0.25,
                'policy_flags': '[]'
            },
            {
                'platform': 'bluesky',
                'account_id': 2,
                'title': 'Entrepreneurship Lessons Learned',
                'body': 'After 5 years of building startups, here are the key lessons I wish I knew earlier. Automation and systematic approaches make a huge difference in scaling your business.',
                'status': 'approved',
                'similarity_score': 0.1,
                'policy_flags': '[]',
                'scheduled_at': (datetime.now() + timedelta(hours=1)).isoformat()
            },
            {
                'platform': 'reddit',
                'account_id': 1,
                'title': 'Productivity Hacks for Entrepreneurs',
                'body': 'Time management is crucial for entrepreneurs. Here are some productivity hacks that have helped me scale my business more efficiently.',
                'status': 'posted',
                'similarity_score': 0.2,
                'policy_flags': '[]',
                'external_uri': 'https://reddit.com/r/entrepreneur/comments/example'
            },
            {
                'platform': 'bluesky',
                'account_id': 2,
                'title': 'This is a test post with blacklisted content',
                'body': 'This post contains politics and spam content that should be flagged by the moderation system.',
                'status': 'draft',
                'similarity_score': 0.1,
                'policy_flags': '["blacklisted_word: politics", "blacklisted_word: spam"]'
            }
        ]
        
        # Insert sample posts
        for post in sample_posts:
            cursor.execute("""
                INSERT INTO posts (platform, account_id, title, body, status, similarity_score, policy_flags, scheduled_at, external_uri)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                post['platform'],
                post['account_id'],
                post['title'],
                post['body'],
                post['status'],
                post['similarity_score'],
                post['policy_flags'],
                post.get('scheduled_at'),
                post.get('external_uri')
            ))
        
        # Add some sample logs
        sample_logs = [
            ('INFO', 'System initialized successfully'),
            ('INFO', 'Sample data created'),
            ('INFO', 'Dashboard started'),
            ('WARNING', 'Rate limit approaching for reddit platform'),
            ('INFO', 'Post 1 approved by admin'),
            ('INFO', 'Post 2 posted successfully to reddit')
        ]
        
        for level, message in sample_logs:
            cursor.execute("""
                INSERT INTO logs (level, message)
                VALUES (?, ?)
            """, (level, message))
        
        conn.commit()
        print(f"✅ Created {len(sample_posts)} sample posts and {len(sample_logs)} log entries")
        print(f"📊 Database initialized at: {db_path}")

if __name__ == "__main__":
    create_sample_data()
