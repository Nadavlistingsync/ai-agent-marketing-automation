#!/usr/bin/env python3
"""
Moderation Dashboard for Xeinst Multi-Channel Poster
Requires manual approval before any content is posted
"""

import os
import json
import hashlib
import sqlite3
import logging
import traceback
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
from dataclasses import dataclass, asdict
from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from pydantic import BaseModel
try:
    import bcrypt
except ImportError:
    bcrypt = None

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/dashboard.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')
QUIET_HOURS = os.getenv('QUIET_HOURS', '23-6')
GLOBAL_MAX_POSTS_PER_HOUR = int(os.getenv('GLOBAL_MAX_POSTS_PER_HOUR', '10'))
MAX_POSTS_PER_ACCOUNT_PER_DAY = int(os.getenv('MAX_POSTS_PER_ACCOUNT_PER_DAY', '5'))
BLACKLIST = os.getenv('BLACKLIST', 'politics,nsfw,spam').split(',')
SIMILARITY_BLOCK_THRESHOLD = float(os.getenv('SIMILARITY_BLOCK_THRESHOLD', '0.8'))
DB_PATH = os.getenv('DATABASE_PATH', 'xeinst_reddit_bot/data/xeinst_bot.db')

# FastAPI app
app = FastAPI(title="Xeinst Moderation Dashboard", version="1.0.0")

# Add CORS middleware for real-time updates
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBasic()

# Rate limiting
from collections import defaultdict
from time import time

# Simple in-memory rate limiter
rate_limiter = defaultdict(list)

def check_rate_limit(client_ip: str, limit: int = 100, window: int = 3600) -> bool:
    """Check if client is within rate limit"""
    now = time()
    # Clean old entries
    rate_limiter[client_ip] = [req_time for req_time in rate_limiter[client_ip] if now - req_time < window]
    
    # Check if under limit
    if len(rate_limiter[client_ip]) >= limit:
        return False
    
    # Add current request
    rate_limiter[client_ip].append(now)
    return True

def get_client_ip(request: Request) -> str:
    """Get client IP address"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"

# Templates
templates = Jinja2Templates(directory="templates")

# Data models
@dataclass
class Post:
    id: int
    platform: str
    account_id: int
    title: str
    body: str
    media_path: Optional[str]
    status: str
    scheduled_at: Optional[datetime]
    external_uri: Optional[str]
    created_at: datetime
    updated_at: datetime
    similarity_score: Optional[float] = None
    policy_flags: Optional[List[str]] = None

@dataclass
class Account:
    id: int
    platform: str
    handle: str
    enabled: bool
    last_post_at: Optional[datetime]

@dataclass
class Review:
    id: int
    post_id: int
    reviewer: str
    action: str
    notes: Optional[str]
    created_at: datetime

@dataclass
class Setting:
    id: int
    key: str
    value: str

@dataclass
class Log:
    id: int
    level: str
    message: str
    meta_json: str
    created_at: datetime

# Database manager
class ModerationDatabase:
    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_database()
    
    def get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_database(self):
        """Initialize moderation database schema"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Posts table - stores all content requiring approval
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
            
            # Accounts table - stores platform accounts
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
            
            # Reviews table - stores approval/rejection history
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
            
            # Settings table - stores configuration
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT NOT NULL UNIQUE,
                    value TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Logs table - stores audit trail
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    level TEXT NOT NULL,
                    message TEXT NOT NULL,
                    meta_json TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_posts_status ON posts (status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_posts_platform ON posts (platform)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_posts_scheduled ON posts (scheduled_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_reviews_post_id ON reviews (post_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_logs_created_at ON logs (created_at)")
            
            # Initialize default settings
            cursor.execute("""
                INSERT OR IGNORE INTO settings (key, value) VALUES 
                ('kill_switch', 'false'),
                ('global_max_posts_per_hour', ?),
                ('max_posts_per_account_per_day', ?),
                ('similarity_block_threshold', ?)
            """, (GLOBAL_MAX_POSTS_PER_HOUR, MAX_POSTS_PER_ACCOUNT_PER_DAY, SIMILARITY_BLOCK_THRESHOLD))
            
            conn.commit()
    
    def get_posts(self, status: str = None, platform: str = None, limit: int = 100) -> List[Post]:
        """Get posts with optional filtering"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            query = "SELECT * FROM posts WHERE 1=1"
            params = []
            
            if status:
                query += " AND status = ?"
                params.append(status)
            
            if platform:
                query += " AND platform = ?"
                params.append(platform)
            
            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            posts = []
            for row in rows:
                post = Post(
                    id=row['id'],
                    platform=row['platform'],
                    account_id=row['account_id'],
                    title=row['title'],
                    body=row['body'],
                    media_path=row['media_path'],
                    status=row['status'],
                    scheduled_at=datetime.fromisoformat(row['scheduled_at']) if row['scheduled_at'] else None,
                    external_uri=row['external_uri'],
                    created_at=datetime.fromisoformat(row['created_at']),
                    updated_at=datetime.fromisoformat(row['updated_at']),
                    similarity_score=row['similarity_score'],
                    policy_flags=json.loads(row['policy_flags']) if row['policy_flags'] else None
                )
                posts.append(post)
            
            return posts
    
    def get_post(self, post_id: int) -> Optional[Post]:
        """Get a specific post"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM posts WHERE id = ?", (post_id,))
            row = cursor.fetchone()
            
            if row:
                return Post(
                    id=row['id'],
                    platform=row['platform'],
                    account_id=row['account_id'],
                    title=row['title'],
                    body=row['body'],
                    media_path=row['media_path'],
                    status=row['status'],
                    scheduled_at=datetime.fromisoformat(row['scheduled_at']) if row['scheduled_at'] else None,
                    external_uri=row['external_uri'],
                    created_at=datetime.fromisoformat(row['created_at']),
                    updated_at=datetime.fromisoformat(row['updated_at']),
                    similarity_score=row['similarity_score'],
                    policy_flags=json.loads(row['policy_flags']) if row['policy_flags'] else None
                )
            return None
    
    def update_post(self, post_id: int, **kwargs) -> bool:
        """Update a post"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            fields = list(kwargs.keys()) + ['updated_at']
            placeholders = ', '.join([f"{field} = ?" for field in fields])
            
            values = list(kwargs.values()) + [datetime.now().isoformat(), post_id]
            
            cursor.execute(f"UPDATE posts SET {placeholders} WHERE id = ?", values)
            conn.commit()
            
            return cursor.rowcount > 0
    
    def create_review(self, post_id: int, reviewer: str, action: str, notes: str = None) -> int:
        """Create a review record"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO reviews (post_id, reviewer, action, notes)
                VALUES (?, ?, ?, ?)
            """, (post_id, reviewer, action, notes))
            
            conn.commit()
            return cursor.lastrowid
    
    def get_reviews(self, post_id: int = None, limit: int = 100) -> List[Review]:
        """Get reviews with optional filtering"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if post_id:
                cursor.execute("SELECT * FROM reviews WHERE post_id = ? ORDER BY created_at DESC", (post_id,))
            else:
                cursor.execute("SELECT * FROM reviews ORDER BY created_at DESC LIMIT ?", (limit,))
            
            rows = cursor.fetchall()
            
            reviews = []
            for row in rows:
                review = Review(
                    id=row['id'],
                    post_id=row['post_id'],
                    reviewer=row['reviewer'],
                    action=row['action'],
                    notes=row['notes'],
                    created_at=datetime.fromisoformat(row['created_at'])
                )
                reviews.append(review)
            
            return reviews
    
    def get_setting(self, key: str) -> Optional[str]:
        """Get a setting value"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
            row = cursor.fetchone()
            return row['value'] if row else None
    
    def update_setting(self, key: str, value: str) -> bool:
        """Update a setting value"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO settings (key, value, created_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            """, (key, value))
            conn.commit()
            return True
    
    def add_log(self, level: str, message: str, meta: Dict = None) -> int:
        """Add a log entry"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            meta_json = json.dumps(meta) if meta else None
            
            cursor.execute("""
                INSERT INTO logs (level, message, meta_json)
                VALUES (?, ?, ?)
            """, (level, message, meta_json))
            
            conn.commit()
            return cursor.lastrowid
    
    def get_logs(self, limit: int = 100) -> List[Log]:
        """Get recent logs"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM logs 
                ORDER BY created_at DESC 
                LIMIT ?
            """, (limit,))
            
            rows = cursor.fetchall()
            
            logs = []
            for row in rows:
                log = Log(
                    id=row['id'],
                    level=row['level'],
                    message=row['message'],
                    meta_json=row['meta_json'],
                    created_at=datetime.fromisoformat(row['created_at'])
                )
                logs.append(log)
            
            return logs
    
    def get_stats(self) -> Dict[str, Any]:
        """Get posting statistics and caps"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get posts count by status
            cursor.execute("""
                SELECT status, COUNT(*) as count FROM posts 
                WHERE created_at >= datetime('now', '-24 hours')
                GROUP BY status
            """)
            status_counts = dict(cursor.fetchall())
            
            # Get posts count by platform
            cursor.execute("""
                SELECT platform, COUNT(*) as count FROM posts 
                WHERE status = 'posted' AND created_at >= datetime('now', '-24 hours')
                GROUP BY platform
            """)
            platform_counts = dict(cursor.fetchall())
            
            # Get hourly posts
            cursor.execute("""
                SELECT COUNT(*) as count FROM posts 
                WHERE status = 'posted' AND created_at >= datetime('now', '-1 hour')
            """)
            hourly_count = cursor.fetchone()['count']
            
            # Get kill switch status
            kill_switch = self.get_setting('kill_switch') == 'true'
            
            return {
                'status_counts': status_counts,
                'platform_counts': platform_counts,
                'hourly_count': hourly_count,
                'kill_switch': kill_switch,
                'caps': {
                    'global_max_posts_per_hour': GLOBAL_MAX_POSTS_PER_HOUR,
                    'max_posts_per_account_per_day': MAX_POSTS_PER_ACCOUNT_PER_DAY,
                    'remaining_hourly': max(0, GLOBAL_MAX_POSTS_PER_HOUR - hourly_count)
                }
            }

# Initialize database
db = ModerationDatabase(DB_PATH)

# Utility functions
def check_similarity(text: str, platform: str) -> float:
    """Calculate similarity score against recent posts"""
    # Simple implementation - in production, use proper embeddings
    recent_posts = db.get_posts(status='posted', platform=platform, limit=10)
    
    if not recent_posts:
        return 0.0
    
    # Simple word overlap similarity
    text_words = set(text.lower().split())
    max_similarity = 0.0
    
    for post in recent_posts:
        post_words = set(post.body.lower().split())
        if text_words and post_words:
            overlap = len(text_words.intersection(post_words))
            similarity = overlap / max(len(text_words), len(post_words))
            max_similarity = max(max_similarity, similarity)
    
    return max_similarity

def check_policy_flags(text: str) -> List[str]:
    """Check for policy violations"""
    flags = []
    text_lower = text.lower()
    
    for word in BLACKLIST:
        if word.strip() in text_lower:
            flags.append(f"blacklisted_word: {word}")
    
    # Add more policy checks as needed
    if len(text) > 1000:
        flags.append("content_too_long")
    
    return flags

def authenticate_user(credentials: HTTPBasicCredentials = Depends(security)) -> bool:
    """Authenticate admin user"""
    return credentials.username == "admin" and credentials.password == ADMIN_PASSWORD

# API endpoints
@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard page"""
    try:
        # Rate limiting
        client_ip = get_client_ip(request)
        if not check_rate_limit(client_ip, limit=60, window=3600):  # 60 requests per hour
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            return HTMLResponse("<h1>Rate limit exceeded. Please try again later.</h1>", status_code=429)
        
        logger.info(f"Loading dashboard page for IP: {client_ip}")
        stats = db.get_stats()
        posts = db.get_posts(status='draft', limit=50)
        
        # Convert Post objects to dictionaries for template rendering
        posts_data = []
        for post in posts:
            post_dict = asdict(post)
            # Convert datetime objects to strings for JSON serialization
            if post_dict.get('created_at'):
                post_dict['created_at'] = post_dict['created_at'].isoformat()
            if post_dict.get('updated_at'):
                post_dict['updated_at'] = post_dict['updated_at'].isoformat()
            if post_dict.get('scheduled_at'):
                post_dict['scheduled_at'] = post_dict['scheduled_at'].isoformat()
            posts_data.append(post_dict)
        
        logger.info(f"Dashboard loaded with {len(posts_data)} posts")
        return templates.TemplateResponse("dashboard_pro.html", {
            "request": request,
            "stats": stats,
            "posts": posts_data,
            "platforms": ["reddit", "bluesky", "twitter", "linkedin"]
        })
    except Exception as e:
        logger.error(f"Dashboard error: {str(e)}")
        logger.error(traceback.format_exc())
        return HTMLResponse(f"<h1>Error: {str(e)}</h1>", status_code=500)

@app.get("/api/queue")
async def get_queue(
    status: str = "draft", 
    platform: str = None, 
    limit: int = 100,
    search: str = None,
    similarity_min: float = None,
    similarity_max: float = None,
    has_policy_flags: bool = None,
    date_from: str = None,
    date_to: str = None
):
    """Get queue of posts with advanced filtering"""
    try:
        logger.info(f"Fetching queue: status={status}, platform={platform}, search={search}")
        
        # Get posts with basic filtering
        posts = db.get_posts(status=status, platform=platform, limit=limit)
        
        # Apply advanced filters
        filtered_posts = []
        for post in posts:
            post_dict = asdict(post)
            
            # Search filter
            if search:
                search_lower = search.lower()
                if not (search_lower in post_dict.get('title', '').lower() or 
                       search_lower in post_dict.get('body', '').lower()):
                    continue
            
            # Similarity filters
            if similarity_min is not None and post_dict.get('similarity_score', 0) < similarity_min:
                continue
            if similarity_max is not None and post_dict.get('similarity_score', 0) > similarity_max:
                continue
            
            # Policy flags filter
            if has_policy_flags is not None:
                has_flags = len(post_dict.get('policy_flags', [])) > 0
                if has_policy_flags != has_flags:
                    continue
            
            # Date filters
            if date_from or date_to:
                created_at = post_dict.get('created_at')
                if created_at:
                    if isinstance(created_at, str):
                        created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    
                    if date_from:
                        from_date = datetime.fromisoformat(date_from)
                        if created_at < from_date:
                            continue
                    
                    if date_to:
                        to_date = datetime.fromisoformat(date_to)
                        if created_at > to_date:
                            continue
            
            # Convert datetime objects to strings
            if post_dict.get('created_at'):
                post_dict['created_at'] = post_dict['created_at'].isoformat()
            if post_dict.get('updated_at'):
                post_dict['updated_at'] = post_dict['updated_at'].isoformat()
            if post_dict.get('scheduled_at'):
                post_dict['scheduled_at'] = post_dict['scheduled_at'].isoformat()
            
            filtered_posts.append(post_dict)
        
        logger.info(f"Returning {len(filtered_posts)} filtered posts")
        return {"posts": filtered_posts}
        
    except Exception as e:
        logger.error(f"Error fetching queue: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/posts/{post_id}/approve")
async def approve_post(post_id: int, scheduled_at: str = None, notes: str = None):
    """Approve a post"""
    post = db.get_post(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    if post.status != 'draft':
        raise HTTPException(status_code=400, detail="Only draft posts can be approved")
    
    # Update post status
    update_data = {"status": "approved"}
    if scheduled_at:
        update_data["scheduled_at"] = scheduled_at
    
    success = db.update_post(post_id, **update_data)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update post")
    
    # Create review record
    db.create_review(post_id, "admin", "approve", notes)
    
    # Log the action
    db.add_log("INFO", f"Post {post_id} approved", {
        "post_id": post_id,
        "platform": post.platform,
        "scheduled_at": scheduled_at,
        "notes": notes
    })
    
    return {"success": True, "message": "Post approved"}

@app.post("/api/posts/{post_id}/reject")
async def reject_post(post_id: int, reason: str):
    """Reject a post"""
    post = db.get_post(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    if post.status != 'draft':
        raise HTTPException(status_code=400, detail="Only draft posts can be rejected")
    
    # Update post status
    success = db.update_post(post_id, status="rejected")
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update post")
    
    # Create review record
    db.create_review(post_id, "admin", "reject", reason)
    
    # Log the action
    db.add_log("INFO", f"Post {post_id} rejected", {
        "post_id": post_id,
        "platform": post.platform,
        "reason": reason
    })
    
    return {"success": True, "message": "Post rejected"}

@app.put("/api/posts/{post_id}")
async def update_post(post_id: int, title: str = None, body: str = None, media_path: str = None):
    """Update post content"""
    post = db.get_post(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    if post.status != 'draft':
        raise HTTPException(status_code=400, detail="Only draft posts can be edited")
    
    # Check similarity and policy
    if body:
        similarity = check_similarity(body, post.platform)
        policy_flags = check_policy_flags(body)
        
        update_data = {
            "body": body,
            "similarity_score": similarity,
            "policy_flags": json.dumps(policy_flags)
        }
    else:
        update_data = {}
    
    if title:
        update_data["title"] = title
    
    if media_path:
        update_data["media_path"] = media_path
    
    if update_data:
        success = db.update_post(post_id, **update_data)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update post")
    
    return {"success": True, "message": "Post updated"}

@app.get("/api/stats")
async def get_stats():
    """Get posting statistics and caps"""
    try:
        logger.info("Fetching dashboard statistics")
        stats = db.get_stats()
        return stats
    except Exception as e:
        logger.error(f"Error fetching stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/events")
async def get_events():
    """Get real-time events stream"""
    async def event_generator():
        while True:
            try:
                # Get latest stats and posts
                stats = db.get_stats()
                recent_posts = db.get_posts(status='draft', limit=10)
                
                # Convert posts to dict format
                posts_data = []
                for post in recent_posts:
                    post_dict = asdict(post)
                    if post_dict.get('created_at'):
                        post_dict['created_at'] = post_dict['created_at'].isoformat()
                    if post_dict.get('updated_at'):
                        post_dict['updated_at'] = post_dict['updated_at'].isoformat()
                    if post_dict.get('scheduled_at'):
                        post_dict['scheduled_at'] = post_dict['scheduled_at'].isoformat()
                    posts_data.append(post_dict)
                
                # Send Server-Sent Events
                event_data = {
                    "stats": stats,
                    "recent_posts": posts_data,
                    "timestamp": datetime.now().isoformat()
                }
                
                yield f"data: {json.dumps(event_data)}\n\n"
                
                # Wait 5 seconds before next update
                import asyncio
                await asyncio.sleep(5)
                
            except Exception as e:
                logger.error(f"Event stream error: {str(e)}")
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
                break
    
    return StreamingResponse(event_generator(), media_type="text/plain")

@app.post("/api/bulk/approve")
async def bulk_approve(request: Request):
    """Bulk approve multiple posts"""
    try:
        data = await request.json()
        post_ids = data.get('post_ids', [])
        scheduled_at = data.get('scheduled_at')
        notes = data.get('notes', 'Bulk approved')
        
        logger.info(f"Bulk approving {len(post_ids)} posts")
        
        approved_count = 0
        failed_posts = []
        
        for post_id in post_ids:
            try:
                success = db.update_post_status(
                    post_id, 
                    'approved', 
                    scheduled_at=scheduled_at,
                    notes=notes
                )
                if success:
                    approved_count += 1
                else:
                    failed_posts.append(post_id)
            except Exception as e:
                logger.error(f"Failed to approve post {post_id}: {str(e)}")
                failed_posts.append(post_id)
        
        logger.info(f"Bulk approval completed: {approved_count} approved, {len(failed_posts)} failed")
        
        return {
            "success": True,
            "approved_count": approved_count,
            "failed_posts": failed_posts,
            "message": f"Approved {approved_count} posts successfully"
        }
        
    except Exception as e:
        logger.error(f"Bulk approval error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/bulk/reject")
async def bulk_reject(request: Request):
    """Bulk reject multiple posts"""
    try:
        data = await request.json()
        post_ids = data.get('post_ids', [])
        reason = data.get('reason', 'Bulk rejected')
        
        logger.info(f"Bulk rejecting {len(post_ids)} posts")
        
        rejected_count = 0
        failed_posts = []
        
        for post_id in post_ids:
            try:
                success = db.update_post_status(post_id, 'rejected', notes=reason)
                if success:
                    rejected_count += 1
                else:
                    failed_posts.append(post_id)
            except Exception as e:
                logger.error(f"Failed to reject post {post_id}: {str(e)}")
                failed_posts.append(post_id)
        
        logger.info(f"Bulk rejection completed: {rejected_count} rejected, {len(failed_posts)} failed")
        
        return {
            "success": True,
            "rejected_count": rejected_count,
            "failed_posts": failed_posts,
            "message": f"Rejected {rejected_count} posts successfully"
        }
        
    except Exception as e:
        logger.error(f"Bulk rejection error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/settings/kill-switch")
async def toggle_kill_switch():
    """Toggle kill switch on/off"""
    current_status = db.get_setting('kill_switch')
    new_status = 'false' if current_status == 'true' else 'true'
    
    db.update_setting('kill_switch', new_status)
    
    # Log the action
    db.add_log("WARNING", f"Kill switch {'enabled' if new_status == 'true' else 'disabled'}")
    
    return {"kill_switch": new_status == 'true'}

@app.get("/api/logs")
async def get_logs(limit: int = 100):
    """Get recent logs"""
    try:
        logs = db.get_logs(limit=limit)
        return {"logs": [asdict(log) for log in logs]}
    except Exception as e:
        logger.error(f"Error fetching logs: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics/performance")
async def get_performance_analytics():
    """Get performance analytics"""
    try:
        # Get posts from last 30 days
        thirty_days_ago = datetime.now() - timedelta(days=30)
        
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Posts by day
            cursor.execute("""
                SELECT DATE(created_at) as date, COUNT(*) as count, status
                FROM posts 
                WHERE created_at >= ?
                GROUP BY DATE(created_at), status
                ORDER BY date DESC
            """, (thirty_days_ago.isoformat(),))
            
            daily_stats = {}
            for row in cursor.fetchall():
                date = row['date']
                if date not in daily_stats:
                    daily_stats[date] = {}
                daily_stats[date][row['status']] = row['count']
            
            # Platform performance
            cursor.execute("""
                SELECT platform, status, COUNT(*) as count
                FROM posts 
                WHERE created_at >= ?
                GROUP BY platform, status
            """, (thirty_days_ago.isoformat(),))
            
            platform_stats = {}
            for row in cursor.fetchall():
                platform = row['platform']
                if platform not in platform_stats:
                    platform_stats[platform] = {}
                platform_stats[platform][row['status']] = row['count']
            
            # Similarity analysis
            cursor.execute("""
                SELECT 
                    CASE 
                        WHEN similarity_score < 0.3 THEN 'low'
                        WHEN similarity_score < 0.7 THEN 'medium'
                        ELSE 'high'
                    END as similarity_level,
                    COUNT(*) as count
                FROM posts 
                WHERE created_at >= ?
                GROUP BY similarity_level
            """, (thirty_days_ago.isoformat(),))
            
            similarity_stats = {}
            for row in cursor.fetchall():
                similarity_stats[row['similarity_level']] = row['count']
            
            # Policy flags analysis
            cursor.execute("""
                SELECT 
                    CASE 
                        WHEN policy_flags = '[]' OR policy_flags IS NULL THEN 'clean'
                        ELSE 'flagged'
                    END as flag_status,
                    COUNT(*) as count
                FROM posts 
                WHERE created_at >= ?
                GROUP BY flag_status
            """, (thirty_days_ago.isoformat(),))
            
            policy_stats = {}
            for row in cursor.fetchall():
                policy_stats[row['flag_status']] = row['count']
        
        return {
            "daily_stats": daily_stats,
            "platform_stats": platform_stats,
            "similarity_stats": similarity_stats,
            "policy_stats": policy_stats,
            "period": "30_days"
        }
        
    except Exception as e:
        logger.error(f"Error fetching performance analytics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check():
    """Professional health check endpoint"""
    try:
        # Check database connection
        db_stats = db.get_stats()
        
        # Check system resources
        import psutil
        import platform
        
        health_data = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
            "database": {
                "status": "connected",
                "posts_count": db_stats.get("status_counts", {}).get("draft", 0) + 
                              db_stats.get("status_counts", {}).get("approved", 0) +
                              db_stats.get("status_counts", {}).get("posted", 0)
            },
            "system": {
                "platform": platform.system(),
                "python_version": platform.python_version(),
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage('/').percent
            },
            "services": {
                "dashboard": "running",
                "api": "running",
                "database": "connected",
                "real_time_updates": "active"
            }
        }
        
        # Check if system is healthy
        if health_data["system"]["cpu_percent"] > 90 or health_data["system"]["memory_percent"] > 90:
            health_data["status"] = "warning"
        
        if health_data["system"]["disk_percent"] > 95:
            health_data["status"] = "critical"
        
        return health_data
        
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }

@app.get("/api/metrics")
async def get_metrics():
    """Professional metrics endpoint for monitoring"""
    try:
        # Get comprehensive metrics
        stats = db.get_stats()
        
        # Calculate additional metrics
        total_posts = sum(stats.get("status_counts", {}).values())
        approval_rate = 0
        if total_posts > 0:
            approved = stats.get("status_counts", {}).get("approved", 0)
            posted = stats.get("status_counts", {}).get("posted", 0)
            approval_rate = ((approved + posted) / total_posts) * 100
        
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "posts": {
                "total": total_posts,
                "draft": stats.get("status_counts", {}).get("draft", 0),
                "approved": stats.get("status_counts", {}).get("approved", 0),
                "posted": stats.get("status_counts", {}).get("posted", 0),
                "rejected": stats.get("status_counts", {}).get("rejected", 0)
            },
            "platforms": stats.get("platform_counts", {}),
            "performance": {
                "approval_rate": round(approval_rate, 2),
                "hourly_limit_remaining": stats.get("caps", {}).get("remaining_hourly", 0),
                "kill_switch": stats.get("kill_switch", False)
            },
            "system": {
                "uptime": "running",
                "last_update": datetime.now().isoformat()
            }
        }
        
        return metrics
        
    except Exception as e:
        logger.error(f"Metrics error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Worker loop for processing approved posts
def process_approved_posts():
    """Process approved posts that are ready to be posted"""
    # Check kill switch
    if db.get_setting('kill_switch') == 'true':
        return
    
    # Check quiet hours
    current_hour = datetime.now().hour
    quiet_start, quiet_end = map(int, QUIET_HOURS.split('-'))
    if quiet_start <= current_hour or current_hour < quiet_end:
        return
    
    # Get approved posts ready for posting
    approved_posts = db.get_posts(status='approved')
    now = datetime.now()
    
    for post in approved_posts:
        if post.scheduled_at and post.scheduled_at <= now:
            # Check rate limits
            stats = db.get_stats()
            if stats['caps']['remaining_hourly'] <= 0:
                break
            
            # Here you would integrate with your actual posting logic
            # For now, just mark as posted
            success = db.update_post(post.id, status="posted")
            if success:
                db.add_log("INFO", f"Post {post.id} posted to {post.platform}")
                
                # Update rate limit
                stats['caps']['remaining_hourly'] -= 1

if __name__ == "__main__":
    print("Starting Xeinst Moderation Dashboard...")
    print(f"Dashboard will be available at: http://localhost:3001")
    print(f"Admin password: {ADMIN_PASSWORD}")
    
    # Start the dashboard
    uvicorn.run(app, host="0.0.0.0", port=3001, reload=True)
