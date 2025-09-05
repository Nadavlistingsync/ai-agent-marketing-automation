# Xeinst Reddit Bot 🤖

A local Reddit automation bot that helps engage with relevant communities using local AI (Ollama) and smart moderation to avoid bans.

## 🚀 Features

- **Local AI Generation**: Uses Ollama with Llama3 for content creation
- **Smart Moderation**: Rule checking, toxicity filtering, and rate limiting
- **Human Approval**: Manual review before posting (with auto-approval option)
- **Subreddit Targeting**: Focus on automation, entrepreneurship, and tech communities
- **Safety First**: Built-in guardrails to avoid shadowbans and mod issues
- **Web Dashboard**: Beautiful web interface to control and monitor the bot

## ⚡ Quick Start (One Command)

### Option 1: Auto-Setup (Recommended)
```bash
# macOS/Linux
./install.sh

# Windows
install.bat

# Or use Python (cross-platform)
python setup_llm.py
```

### Option 2: Make Commands
```bash
# Complete setup including LLM
make full-setup

# Or step by step
make setup-llm-auto  # Install Ollama + download Llama3
make setup           # Install Python deps + seed database
```

## 🌐 Web Dashboard

The bot includes a beautiful web dashboard for easy control and monitoring:

```bash
# Start the dashboard
make dashboard

# Or use the script
./start_dashboard.sh

# Or run manually
python web_dashboard.py
```

**Dashboard Features:**
- 📊 Real-time bot status and statistics
- 🎛️ Start/stop bot controls
- 📝 Queue management (approve/skip/delete drafts)
- 🔍 Run monitor and post scheduler manually
- 🧪 Test Reddit API and Ollama connections
- 📈 View recent activity and daily stats
- ⚙️ System health monitoring
- 🌱 Database seeding and configuration

**Access the dashboard at:** http://localhost:5000

## 🛠️ Manual Setup (10 minutes)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Create Reddit App
1. Go to [Reddit App Preferences](https://www.reddit.com/prefs/apps)
2. Click "Create App" → "script"
3. Note your `client_id` and `client_secret`

### 3. Install Ollama
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Start Ollama service
ollama serve

# Pull Llama3 model
ollama pull llama3
```

### 4. Configure Environment
```bash
cp env.example .env
# Edit .env with your Reddit credentials
```

**Required Environment Variables:**
```bash
# Reddit API Credentials (Required)
REDDIT_CLIENT_ID=your_client_id_here
REDDIT_CLIENT_SECRET=your_client_secret_here
REDDIT_USERNAME=your_reddit_username
REDDIT_PASSWORD=your_reddit_password
REDDIT_USER_AGENT=XeinstBot/1.0 (by /u/your_username)

# Ollama Configuration (Required)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3
```

### 5. Seed Initial Data
```bash
make seed
```

### 6. Start the Bot
```bash
# Development mode (watcher + scheduler)
make dev

# Or run manually
python scheduler.py

# Or use the web dashboard
make dashboard
```

## 📁 Project Structure

```
xeinst_reddit_bot/
├── config.py          # Configuration loader
├── db.py             # Database operations
├── reddit_client.py  # Reddit API client
├── llm.py           # Ollama integration
├── moderation.py    # Content moderation
├── scheduler.py     # Task scheduling
├── cli.py          # Command line interface
├── web_dashboard.py # Web dashboard server
├── setup_llm.py    # LLM setup script
├── install.sh      # macOS/Linux installer
├── install.bat     # Windows installer
├── start_dashboard.sh # Dashboard startup script
├── templates/      # HTML templates
│   └── dashboard.html
├── prompts/        # AI prompts and examples
├── tests/          # Unit tests
├── data/           # SQLite database
├── logs/           # Application logs
├── env.example     # Environment template
├── config.yaml     # Configuration file
├── requirements.txt # Python dependencies
└── Makefile        # Development commands
```

## 🎯 Target Subreddits

- r/Entrepreneur
- r/startups  
- r/SideProject
- r/automate
- r/lowcode
- r/nocode
- r/selfhosted
- r/datascience
- r/marketingautomation

## 🔑 Target Keywords

- "automation"
- "Zapier"
- "n8n" 
- "Make.com"
- "webhook"
- "agent marketplace"
- "AI agent"
- "cold outreach"
- "lead gen"

## 🚦 Safety Features

- **Rate Limiting**: Global 90-150s between actions
- **Per-Sub Cooldowns**: 12-24h after top-level posts
- **Content Length**: <120 words default, <60 for quick replies
- **Link Policy**: Only when explicitly requested
- **Moderation**: Respects "No self-promo" flairs
- **Shadowban Detection**: Periodic visibility checks

## 📊 Usage

### Web Dashboard (Recommended)
```bash
make dashboard
# Open http://localhost:5000 in your browser
```

### Command Line Interface
```bash
# Monitor and Queue
python cli.py queue:list
python cli.py queue:approve <id>
python cli.py queue:skip <id>

# Manual Posting
python cli.py post:now --text "Your text" --sub r/entrepreneur
```

### Development
```bash
make dev      # Run watcher + scheduler
make seed     # Seed example data
make test     # Run unit tests
```

### System Checks
```bash
make full-check     # Check everything
make check-env      # Check environment
make check-ollama   # Check Ollama status
make check-reddit   # Check Reddit credentials
```

## ⚠️ Important Notes

- **Always test in low-risk subreddits first**
- **Monitor mod feedback and adjust behavior**
- **Respect Reddit's terms of service**
- **Start with manual approval mode**
- **Keep engagement helpful and non-promotional**

## 🔧 Configuration

Edit `config.yaml` to customize:
- Target subreddits and keywords
- Posting schedules and cooldowns
- Content length limits
- Rate limiting rules

## 📈 Monitoring

The bot provides:
- Daily activity reports
- Karma tracking
- Mod feedback logging
- Rate limit status
- Error monitoring
- Real-time web dashboard

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details

---

**Remember**: This bot is for educational and legitimate engagement purposes. Always follow Reddit's rules and community guidelines.
