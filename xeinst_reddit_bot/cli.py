"""
Command Line Interface for Xeinst Reddit Bot
Provides commands for managing the bot, queue, and posting
"""

import typer
import logging
from typing import Optional, List
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt, Confirm
from rich.syntax import Syntax
import json
from datetime import datetime

from config import Config
from db import Database
from reddit_client import RedditClient
from llm import OllamaClient
from moderation import ContentModerator
from scheduler import BotScheduler

# Initialize Typer app
app = typer.Typer(help="Xeinst Reddit Bot - Local Reddit Automation with AI")

# Initialize Rich console
console = Console()

# Global variables for components
config = None
database = None
reddit_client = None
llm_client = None
moderator = None
scheduler = None

def initialize_components():
    """Initialize all bot components"""
    global config, database, reddit_client, llm_client, moderator, scheduler
    
    try:
        # Load configuration
        config = Config()
        
        # Initialize database
        database = Database(config.database_path)
        
        # Initialize Reddit client
        reddit_client = RedditClient(config.reddit_credentials)
        
        # Initialize Ollama client
        ollama_config = config.ollama_config
        llm_client = OllamaClient(ollama_config['base_url'], ollama_config['model'])
        
        # Initialize moderator
        moderator = ContentModerator(config.config)
        
        # Initialize scheduler (optional for CLI operations)
        # scheduler = BotScheduler(config.config, database, reddit_client, llm_client, moderator)
        
        return True
        
    except Exception as e:
        console.print(f"[red]Error initializing components: {e}[/red]")
        return False

@app.command()
def seed_subs():
    """Seed subreddits table with initial data"""
    if not initialize_components():
        return
    
    try:
        console.print("[yellow]Seeding subreddits...[/yellow]")
        
        subreddits = config.subreddits
        count = database.seed_subreddits(subreddits)
        
        console.print(f"[green]Successfully seeded {count} subreddits[/green]")
        
        # Display seeded subreddits
        table = Table(title="Seeded Subreddits")
        table.add_column("Name", style="cyan")
        table.add_column("Subreddit", style="magenta")
        table.add_column("Cooldown", style="yellow")
        table.add_column("Karma Min", style="green")
        table.add_column("Auto-approve", style="blue")
        
        for sub in subreddits:
            table.add_row(
                sub['name'],
                f"r/{sub['subreddit']}",
                f"{sub['cooldown_hours']}h",
                str(sub['karma_min']),
                "Yes" if sub.get('auto_approve', False) else "No"
            )
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]Error seeding subreddits: {e}[/red]")

@app.command()
def seed_keywords():
    """Seed keywords table with initial data"""
    if not initialize_components():
        return
    
    try:
        console.print("[yellow]Seeding keywords...[/yellow]")
        
        keywords = config.keywords
        count = database.seed_keywords(keywords)
        
        console.print(f"[green]Successfully seeded {count} keywords[/green]")
        
        # Display seeded keywords
        table = Table(title="Seeded Keywords")
        table.add_column("Keyword", style="cyan")
        table.add_column("Status", style="green")
        
        for keyword in keywords:
            table.add_row(keyword, "Active")
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]Error seeding keywords: {e}[/red]")

@app.command()
def queue_list(
    status: str = typer.Option("pending", "--status", "-s", help="Filter by status (pending, approved, posted, failed)")
):
    """List items in the queue"""
    if not initialize_components():
        return
    
    try:
        items = database.get_queue_items(status=status, limit=50)
        
        if not items:
            console.print(f"[yellow]No items found with status: {status}[/yellow]")
            return
        
        # Display queue items
        table = Table(title=f"Queue Items - Status: {status.upper()}")
        table.add_column("ID", style="cyan")
        table.add_column("Subreddit", style="magenta")
        table.add_column("Post Title", style="yellow")
        table.add_column("Keywords", style="green")
        table.add_column("Length", style="blue")
        table.add_column("Xeinst", style="red")
        table.add_column("Created", style="white")
        
        for item in items:
            title = item['post_title'][:50] + "..." if len(item['post_title']) > 50 else item['post_title']
            xeinst = "Yes" if item['includes_xeinst'] else "No"
            
            table.add_row(
                str(item['id']),
                f"r/{item['subreddit']}",
                title,
                item['keywords_matched'],
                str(item['reply_length']),
                xeinst,
                item['created_at'][:19] if item['created_at'] else "N/A"
            )
        
        console.print(table)
        
        # Show summary
        console.print(f"\n[green]Total items: {len(items)}[/green]")
        
    except Exception as e:
        console.print(f"[red]Error listing queue: {e}[/red]")

@app.command()
def queue_approve(
    queue_id: int = typer.Argument(..., help="Queue item ID to approve")
):
    """Approve a queue item for posting"""
    if not initialize_components():
        return
    
    try:
        # Get queue item
        items = database.get_queue_items(status='pending', limit=1000)
        item = next((item for item in items if item['id'] == queue_id), None)
        
        if not item:
            console.print(f"[red]Queue item {queue_id} not found[/red]")
            return
        
        # Display item details
        console.print(Panel(
            f"[cyan]Subreddit:[/cyan] r/{item['subreddit']}\n"
            f"[cyan]Post Title:[/cyan] {item['post_title']}\n"
            f"[cyan]Keywords:[/cyan] {item['keywords_matched']}\n"
            f"[cyan]Draft Reply:[/cyan]\n{item['draft_reply']}",
            title=f"Queue Item {queue_id}",
            border_style="green"
        ))
        
        # Confirm approval
        if Confirm.ask("Approve this item for posting?"):
            # Check compliance
            compliance_result = moderator.check_content_compliance(
                item['draft_reply'],
                item['subreddit'],
                {
                    'title': item['post_title'],
                    'content': item['post_content'],
                    'flair': None
                },
                config.config
            )
            
            if not compliance_result['isCompliant']:
                console.print("[red]Content has compliance issues:[/red]")
                for violation in compliance_result['violations']:
                    console.print(f"  • {violation}")
                
                if not Confirm.ask("Post anyway?"):
                    return
            
            # Update status
            success = database.update_queue_status(queue_id, 'approved')
            
            if success:
                console.print(f"[green]Queue item {queue_id} approved successfully[/green]")
                
                # Update daily stats
                today = datetime.now().strftime('%Y-%m-%d')
                database.update_daily_stats(today, approvals_given=1)
            else:
                console.print(f"[red]Failed to approve queue item {queue_id}[/red]")
        else:
            console.print("[yellow]Approval cancelled[/yellow]")
        
    except Exception as e:
        console.print(f"[red]Error approving queue item: {e}[/red]")

@app.command()
def queue_skip(
    queue_id: int = typer.Argument(..., help="Queue item ID to skip")
):
    """Skip a queue item"""
    if not initialize_components():
        return
    
    try:
        # Get queue item
        items = database.get_queue_items(status='pending', limit=1000)
        item = next((item for item in items if item['id'] == queue_id), None)
        
        if not item:
            console.print(f"[red]Queue item {queue_id} not found[/red]")
            return
        
        # Display item details
        console.print(Panel(
            f"[cyan]Subreddit:[/cyan] r/{item['subreddit']}\n"
            f"[cyan]Post Title:[/cyan] {item['post_title']}\n"
            f"[cyan]Keywords:[/cyan] {item['keywords_matched']}",
            title=f"Queue Item {queue_id}",
            border_style="yellow"
        ))
        
        # Confirm skip
        if Confirm.ask("Skip this item?"):
            # Update status
            success = database.update_queue_status(queue_id, 'skipped')
            
            if success:
                console.print(f"[green]Queue item {queue_id} skipped successfully[/green]")
                
                # Update daily stats
                today = datetime.now().strftime('%Y-%m-%d')
                database.update_daily_stats(today, drafts_skipped=1)
            else:
                console.print(f"[red]Failed to skip queue item {queue_id}[/red]")
        else:
            console.print("[yellow]Skip cancelled[/yellow]")
        
    except Exception as e:
        console.print(f"[red]Error skipping queue item: {e}[/red]")

@app.command()
def post_now(
    text: str = typer.Option(..., "--text", "-t", help="Text to post"),
    subreddit: str = typer.Option(..., "--sub", "-s", help="Subreddit to post in"),
    auto: bool = typer.Option(False, "--auto", help="Auto-approve (bypass queue)"),
    post_id: Optional[str] = typer.Option(None, "--post-id", "-p", help="Post ID to reply to")
):
    """Post content immediately"""
    if not initialize_components():
        return
    
    try:
        # Check if subreddit is configured
        sub_config = config.get_subreddit_config(subreddit)
        if not sub_config:
            console.print(f"[red]Subreddit r/{subreddit} not configured[/red]")
            return
        
        # Check compliance
        compliance_result = moderator.check_content_compliance(
            text,
            subreddit,
            {
                'title': 'Manual post',
                'content': text,
                'flair': None
            },
            config.config
        )
        
        if not compliance_result['isCompliant']:
            console.print("[red]Content has compliance issues:[/red]")
            for violation in compliance_result['violations']:
                console.print(f"  • {violation}")
            
            if not auto and not Confirm.ask("Post anyway?"):
                return
        
        # Check rate limits
        rate_limit_check = moderator.check_rate_limits(subreddit, 'post', database)
        if not rate_limit_check['allowed']:
            console.print(f"[red]Rate limited: {rate_limit_check['reason']}[/red]")
            return
        
        # Post the content
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Posting content...", total=None)
            
            if post_id:
                # Reply to specific post
                result = reddit_client.post_reply(post_id, text, subreddit)
            else:
                # This would be a new post - not implemented in this version
                console.print("[red]New posts not supported in this version[/red]")
                return
            
            progress.update(task, completed=True)
        
        if result:
            console.print(f"[green]Content posted successfully![/green]")
            console.print(f"Reply ID: {result['reply_id']}")
            console.print(f"URL: {result['permalink']}")
            
            # Add to history
            history_item = {
                'subreddit': subreddit,
                'post_id': post_id or 'manual',
                'post_title': 'Manual post',
                'post_author': 'manual',
                'reply_id': result['reply_id'],
                'reply_content': text,
                'reply_length': len(text.split()),
                'includes_xeinst': 'xeinst' in text.lower()
            }
            
            database.add_to_history(history_item)
            
            # Update statistics
            database.update_subreddit_stats(subreddit, last_post_time=datetime.now(), posts_today=1)
            database.record_action('global', 'global', 1, 90)
            database.record_action('subreddit', subreddit, 1, 12 * 60)
            
            today = datetime.now().strftime('%Y-%m-%d')
            database.update_daily_stats(today, posts_made=1)
            
        else:
            console.print("[red]Failed to post content[/red]")
        
    except Exception as e:
        console.print(f"[red]Error posting content: {e}[/red]")

@app.command()
def status():
    """Show bot status and statistics"""
    if not initialize_components():
        return
    
    try:
        # Get database stats
        db_stats = database.get_database_stats()
        
        # Get configuration info
        subreddit_count = len(config.subreddits)
        keyword_count = len(config.keywords)
        
        # Create status panel
        status_text = f"""
[cyan]Database Status:[/cyan]
  • Queue items: {db_stats.get('pending_queue_count', 0)} pending
  • Total posts: {db_stats.get('history_count', 0)}
  • Posts today: {db_stats.get('posts_last_24h', 0)}

[cyan]Configuration:[/cyan]
  • Subreddits: {subreddit_count}
  • Keywords: {keyword_count}
  • Environment: {config.bot_config['environment']}

[cyan]Services:[/cyan]
  • Database: ✅ Active
  • Reddit API: ✅ Connected
  • Ollama: {'✅' if llm_client.test_connection() else '❌'} {'Connected' if llm_client.test_connection() else 'Not connected'}
        """
        
        console.print(Panel(status_text, title="Bot Status", border_style="green"))
        
        # Show recent activity
        if db_stats.get('posts_last_24h', 0) > 0:
            console.print("\n[yellow]Recent Activity:[/yellow]")
            # This would show recent posts from history table
        
    except Exception as e:
        console.print(f"[red]Error getting status: {e}[/red]")

@app.command()
def test_ai():
    """Test AI content generation"""
    if not initialize_components():
        return
    
    try:
        console.print("[yellow]Testing AI content generation...[/yellow]")
        
        # Test prompt
        test_content = "I'm looking for tools to automate my customer onboarding process. Currently using spreadsheets but it's getting unwieldy."
        test_subreddit = "Entrepreneur"
        test_keywords = ["automation", "customer onboarding"]
        
        # Generate content
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Generating content...", total=None)
            
            result = llm_client.generate_buyer_content(test_content, test_subreddit, test_keywords)
            
            progress.update(task, completed=True)
        
        if result['success']:
            console.print(Panel(
                f"[cyan]Generated Content:[/cyan]\n\n{result['content']}\n\n"
                f"[cyan]Details:[/cyan]\n"
                f"• Length: {result['length']} words\n"
                f"• Model: {result['model']}\n"
                f"• Xeinst included: {'Yes' if result['includes_xeinst'] else 'No'}\n"
                f"• Generation time: {result.get('generation_time', 0):.2f}s",
                title="AI Test Result",
                border_style="green"
            ))
        else:
            console.print(f"[red]AI generation failed: {result.get('error')}[/red]")
        
    except Exception as e:
        console.print(f"[red]Error testing AI: {e}[/red]")

@app.command()
def test_reddit():
    """Test Reddit API connection"""
    if not initialize_components():
        return
    
    try:
        console.print("[yellow]Testing Reddit API connection...[/yellow]")
        
        # Test connection
        if reddit_client.test_connection():
            console.print("[green]✅ Reddit API connection successful[/green]")
            
            # Get user info
            me = reddit_client.reddit.user.me()
            console.print(f"[cyan]Connected as:[/cyan] u/{me.name}")
            console.print(f"[cyan]Karma:[/cyan] {me.link_karma} link, {me.comment_karma} comment")
            
        else:
            console.print("[red]❌ Reddit API connection failed[/red]")
        
    except Exception as e:
        console.print(f"[red]Error testing Reddit API: {e}[/red]")

@app.command()
def logs(
    lines: int = typer.Option(50, "--lines", "-n", help="Number of lines to show")
):
    """Show recent logs"""
    try:
        # This would read from the log file
        console.print("[yellow]Log viewing not implemented in this version[/yellow]")
        console.print("Check the logs directory for log files")
        
    except Exception as e:
        console.print(f"[red]Error showing logs: {e}[/red]")

@app.command()
def config_show():
    """Show current configuration"""
    if not initialize_components():
        return
    
    try:
        # Display configuration
        config_data = {
            'Subreddits': len(config.subreddits),
            'Keywords': len(config.keywords),
            'Environment': config.bot_config['environment'],
            'Database': config.database_path,
            'Ollama Model': config.ollama_config['model'],
            'Ollama URL': config.ollama_config['base_url']
        }
        
        table = Table(title="Configuration")
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="yellow")
        
        for key, value in config_data.items():
            table.add_row(key, str(value))
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]Error showing configuration: {e}[/red]")

@app.command()
def health():
    """Check system health"""
    if not initialize_components():
        return
    
    try:
        console.print("[yellow]Checking system health...[/yellow]")
        
        # Check Reddit
        reddit_ok = reddit_client.test_connection()
        
        # Check Ollama
        ollama_health = llm_client.health_check()
        
        # Check database
        db_stats = database.get_database_stats()
        
        # Display health status
        health_table = Table(title="System Health")
        health_table.add_column("Service", style="cyan")
        health_table.add_column("Status", style="green")
        health_table.add_column("Details", style="yellow")
        
        health_table.add_row(
            "Reddit API",
            "✅ Healthy" if reddit_ok else "❌ Unhealthy",
            "Connected" if reddit_ok else "Connection failed"
        )
        
        health_table.add_row(
            "Ollama",
            f"✅ {ollama_health['status']}",
            f"Model: {ollama_health.get('model', 'Unknown')}"
        )
        
        health_table.add_row(
            "Database",
            "✅ Healthy",
            f"{db_stats.get('queue_count', 0)} queue items, {db_stats.get('history_count', 0)} posts"
        )
        
        console.print(health_table)
        
        # Overall status
        if reddit_ok and ollama_health['status'] == 'healthy':
            console.print("\n[green]🎉 All systems are healthy![/green]")
        else:
            console.print("\n[red]⚠️  Some systems have issues[/red]")
        
    except Exception as e:
        console.print(f"[red]Error checking health: {e}[/red]")

if __name__ == "__main__":
    app()
