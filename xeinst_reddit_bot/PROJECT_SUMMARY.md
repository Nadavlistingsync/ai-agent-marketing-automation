# Xeinst Reddit Bot - Project Summary

## 🎯 What Was Built

A complete, local Reddit automation bot that runs entirely on your machine using:
- **Ollama** for local AI content generation (no API costs)
- **PRAW** for Reddit API interaction
- **SQLite** for local data storage
- **APScheduler** for automated task management
- **Rich** for beautiful CLI interface

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Reddit API    │    │   Local AI      │    │   Database      │
│   (PRAW)       │◄──►│   (Ollama)      │◄──►│   (SQLite)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Reddit Client  │    │   LLM Client    │    │   Database      │
│                 │    │                 │    │   Manager       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │     Scheduler           │
                    │  (APScheduler)         │
                    └─────────────────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │   Content Moderation    │
                    │   & Safety Checks      │
                    └─────────────────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │      CLI Interface      │
                    │      (Typer + Rich)    │
                    └─────────────────────────┘
```

## 📁 File Structure

```
xeinst_reddit_bot/
├── 📄 README.md                    # Main documentation
├── 📄 PROJECT_SUMMARY.md           # This file
├── 📄 requirements.txt             # Python dependencies
├── 📄 env.example                  # Environment template
├── 📄 config.yaml                  # Configuration file
├── 📄 Makefile                     # Development commands
├── 🐍 config.py                    # Configuration loader
├── 🐍 db.py                        # Database operations
├── 🐍 reddit_client.py             # Reddit API client
├── 🐍 llm.py                       # Ollama integration
├── 🐍 moderation.py                # Content safety
├── 🐍 scheduler.py                 # Task automation
├── 🐍 cli.py                       # Command interface
├── 🐍 quick_start.py               # Setup helper
├── 🐍 run_tests.py                 # Test runner
├── 📁 prompts/                     # AI prompts
│   ├── system.txt                  # Main system prompt
│   ├── reply_example_automation.txt
│   └── reply_example_entrepreneur.txt
├── 📁 tests/                       # Unit tests
│   ├── __init__.py
│   └── test_db.py
├── 📁 data/                        # SQLite database
└── 📁 logs/                        # Application logs
```

## 🚀 Key Features

### 🤖 AI-Powered Content Generation
- Uses local Llama3 model via Ollama
- Generates context-aware responses
- Includes few-shot examples for better quality
- Automatically determines when to mention Xeinst

### 🛡️ Safety & Compliance
- Content toxicity filtering
- Spam detection
- Rate limiting (global + per-subreddit)
- Subreddit rule compliance
- FTC compliance checks

### 📊 Smart Automation
- Monitors target subreddits for keywords
- Creates draft replies automatically
- Human approval workflow
- Scheduled posting with cooldowns
- Daily activity reports

### 🎯 Targeted Engagement
- Focuses on automation/entrepreneurship communities
- Keyword-based post detection
- Intent classification (buyer/seller/promoter)
- Respects subreddit-specific rules

## 🔧 How It Works

### 1. **Monitoring Phase**
- Bot scans target subreddits every 15 minutes
- Searches for posts matching configured keywords
- Generates AI-powered draft replies
- Adds drafts to approval queue

### 2. **Approval Phase**
- Human reviews draft replies
- Approves, skips, or modifies content
- Compliance checks run automatically
- Rate limits are enforced

### 3. **Posting Phase**
- Approved content is posted automatically
- Respects posting hours and cooldowns
- Tracks all activity in database
- Monitors for mod feedback

### 4. **Maintenance Phase**
- Daily activity reports
- Database cleanup (90-day retention)
- Health checks and monitoring
- Shadowban detection

## 🎮 Usage Examples

### Start the Bot
```bash
# Quick setup
python quick_start.py

# Start scheduler
make dev

# Or manually
python scheduler.py
```

### Manage Content
```bash
# List pending drafts
python cli.py queue:list

# Approve a draft
python cli.py queue:approve 123

# Skip a draft
python cli.py queue:skip 123

# Post manually
python cli.py post:now --text "Your text" --sub r/entrepreneur
```

### Monitor Status
```bash
# Check bot status
python cli.py status

# System health
python cli.py health

# Configuration
python cli.py config:show
```

### Testing
```bash
# Run tests
python run_tests.py

# Test AI generation
python cli.py test-ai

# Test Reddit connection
python cli.py test-reddit
```

## ⚙️ Configuration

### Environment Variables (.env)
```bash
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret
REDDIT_USERNAME=your_username
REDDIT_PASSWORD=your_password
REDDIT_USER_AGENT=XeinstBot/1.0
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3
```

### Main Config (config.yaml)
- **Subreddits**: Target communities with rules
- **Keywords**: Search terms to monitor
- **Rate Limits**: Posting frequency controls
- **Content Rules**: Length, safety, compliance
- **Scheduling**: Monitoring and posting intervals

## 🚦 Safety Features

### Rate Limiting
- Global: 90-150 seconds between actions
- Per-subreddit: 12-24 hours between posts
- Daily limits: 10 posts, 50 comments max

### Content Safety
- Toxicity filtering
- Spam detection
- Repetition checking
- Link validation
- Flair compliance

### Compliance
- FTC disclosure requirements
- Subreddit-specific rules
- "No self-promo" flair respect
- Mod feedback monitoring

## 🔍 Monitoring & Analytics

### Daily Reports
- Posts made and comments
- Karma gained
- Approvals given
- Errors encountered
- Xeinst mentions

### Database Tracking
- Queue status and history
- Rate limit usage
- Mod feedback logs
- Keyword performance
- Subreddit activity

## 🛠️ Development

### Makefile Commands
```bash
make help          # Show all commands
make dev           # Start development mode
make seed          # Seed initial data
make test          # Run tests
make clean         # Clean up files
make setup         # Complete setup
```

### Testing
- Unit tests for database operations
- Import validation
- Basic functionality checks
- CLI command testing

## 📈 Performance

### Scalability
- Local execution (no cloud costs)
- Efficient SQLite database
- Configurable monitoring intervals
- Rate-limited API usage

### Resource Usage
- Minimal CPU when idle
- ~100MB RAM base usage
- Database grows with activity
- Log rotation (10MB max, 5 backups)

## 🔮 Future Enhancements

### Potential Additions
- Web dashboard interface
- Advanced analytics
- Multi-account support
- Content templates
- A/B testing
- Integration APIs

### Extensibility
- Plugin system for new features
- Custom content generators
- Additional AI models
- Social media expansion

## ⚠️ Important Notes

### Legal Compliance
- Follows Reddit's Terms of Service
- Respects community guidelines
- Includes required disclosures
- Monitors mod feedback

### Best Practices
- Start with low-risk subreddits
- Monitor feedback closely
- Adjust behavior based on results
- Keep engagement helpful and non-promotional

### Limitations
- Single Reddit account per instance
- Local AI model quality depends on hardware
- Manual approval required by default
- No cross-platform posting

## 🎉 Getting Started

1. **Install dependencies**: `pip install -r requirements.txt`
2. **Setup Ollama**: `ollama serve && ollama pull llama3`
3. **Configure Reddit**: Copy `env.example` to `.env` and fill credentials
4. **Quick start**: `python quick_start.py`
5. **Start bot**: `make dev`
6. **Monitor queue**: `python cli.py queue:list`

## 📚 Resources

- **README.md**: Complete setup and usage guide
- **Makefile**: All available commands
- **CLI Help**: `python cli.py --help`
- **Test Runner**: `python run_tests.py`
- **Quick Start**: `python quick_start.py`

---

**Built with ❤️ for local, safe, and effective Reddit automation**
