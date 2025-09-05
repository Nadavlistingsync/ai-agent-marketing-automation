# 🏠 Local Setup Guide - Complete System

## 🎯 For Running Locally on New Computer

This guide will help you set up the complete Xeinst Ambassador Automation system to run locally on your new computer.

## 📋 Prerequisites

### **System Requirements:**
- Python 3.8+ installed
- Internet connection (for API calls)
- 2GB+ free disk space
- Modern web browser

### **API Accounts Needed:**
- Reddit Developer Account (for Reddit API)
- Bluesky Account (for Bluesky API)
- OpenAI Account (optional, for AI features)

## 🚀 Complete Setup Process

### **Step 1: Copy Code Files**
Copy these files to your new computer:
```
Xeinst Ambasdor Automation/
├── moderation_dashboard.py
├── moderation_worker.py
├── create_sample_data.py
├── bluesky_client.py
├── requirements_moderation.txt
├── env.moderation.example
├── templates/
│   ├── dashboard.html
│   └── dashboard_pro.html
├── xeinst_reddit_bot/
│   ├── config.py
│   ├── db.py
│   ├── moderation.py
│   ├── reddit_client.py
│   ├── llm.py
│   ├── scheduler.py
│   ├── cli.py
│   ├── config.yaml
│   ├── requirements.txt
│   ├── env.example
│   └── prompts/
│       ├── system.txt
│       ├── reply_example_automation.txt
│       └── reply_example_entrepreneur.txt
├── README.md
├── PROFESSIONAL_SYSTEM.md
└── .gitignore
```

### **Step 2: Create Virtual Environment**
```bash
# Navigate to project directory
cd "Xeinst Ambasdor Automation"

# Create virtual environment
python3 -m venv xeinst_reddit_bot/venv

# Activate virtual environment
# On macOS/Linux:
source xeinst_reddit_bot/venv/bin/activate

# On Windows:
xeinst_reddit_bot\venv\Scripts\activate
```

### **Step 3: Install Dependencies**
```bash
# Install all required packages
pip install -r requirements_moderation.txt
pip install -r xeinst_reddit_bot/requirements.txt

# Install additional system monitoring
pip install psutil
```

### **Step 4: Set Up Environment Variables**
```bash
# Copy environment templates
cp env.moderation.example .env
cp xeinst_reddit_bot/env.example xeinst_reddit_bot/.env
```

**Edit .env file with your credentials:**
```bash
# Reddit API (get from https://www.reddit.com/prefs/apps)
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
REDDIT_USERNAME=your_reddit_username
REDDIT_PASSWORD=your_reddit_password

# Bluesky API (get from https://bsky.app)
BLUESKY_IDENTIFIER=your_bluesky_handle
BLUESKY_PASSWORD=your_bluesky_app_password
BLUESKY_SERVICE_URL=https://bsky.social

# Dashboard Security
DASHBOARD_USERNAME=admin
DASHBOARD_PASSWORD=your_secure_password_here

# AI/LLM (optional)
OPENAI_API_KEY=your_openai_key
OLLAMA_BASE_URL=http://localhost:11434
```

### **Step 5: Initialize Database**
```bash
# Create sample data and initialize database
python create_sample_data.py
```

### **Step 6: Start the System**
```bash
# Start the professional dashboard
uvicorn moderation_dashboard:app --host 0.0.0.0 --port 3001
```

## 🌐 Access Your Local System

### **Dashboard URLs:**
- **Main Dashboard**: http://localhost:3001
- **Health Check**: http://localhost:3001/api/health
- **Performance Metrics**: http://localhost:3001/api/metrics
- **Analytics**: http://localhost:3001/api/analytics/performance

### **Login Credentials:**
- **Username**: admin
- **Password**: (whatever you set in .env file)

## 🔧 Local System Features

### **What Runs Locally:**
- ✅ **Web Dashboard** - Professional interface
- ✅ **Database** - SQLite database (local file)
- ✅ **API Endpoints** - All 15+ endpoints
- ✅ **Real-time Updates** - Live data streaming
- ✅ **Content Moderation** - AI-powered filtering
- ✅ **Multi-platform Support** - Reddit + Bluesky
- ✅ **Health Monitoring** - System metrics
- ✅ **Analytics** - Performance reporting

### **What Connects to Internet:**
- 🌐 **Reddit API** - For posting to Reddit
- 🌐 **Bluesky API** - For posting to Bluesky
- 🌐 **AI Services** - For content generation (if enabled)

## 🛠️ Local Development Commands

### **Start Dashboard:**
```bash
source xeinst_reddit_bot/venv/bin/activate
uvicorn moderation_dashboard:app --host 0.0.0.0 --port 3001
```

### **Start Background Worker:**
```bash
source xeinst_reddit_bot/venv/bin/activate
python moderation_worker.py
```

### **Run Reddit Bot:**
```bash
source xeinst_reddit_bot/venv/bin/activate
python xeinst_reddit_bot/cli.py
```

### **Check System Health:**
```bash
curl http://localhost:3001/api/health
```

## 📊 Local System Monitoring

### **Health Check:**
```bash
curl http://localhost:3001/api/health
```

### **Performance Metrics:**
```bash
curl http://localhost:3001/api/metrics
```

### **View Logs:**
```bash
# Dashboard logs
tail -f logs/dashboard.log

# System logs
tail -f logs/system.log
```

## 🔒 Local Security

### **Firewall Settings:**
- **Port 3001** - Dashboard access (localhost only)
- **No external ports** - System runs locally only

### **Data Storage:**
- **Database**: `xeinst_reddit_bot/data/xeinst_bot.db` (local file)
- **Logs**: `logs/` directory (local files)
- **No cloud storage** - Everything stays on your computer

## 🚀 Quick Start Script

Create this script to start everything:

```bash
#!/bin/bash
# start_local_system.sh

echo "🚀 Starting Xeinst Ambassador Automation (Local)"
echo "================================================"

# Activate virtual environment
source xeinst_reddit_bot/venv/bin/activate

# Start dashboard
echo "🌐 Starting dashboard on http://localhost:3001"
uvicorn moderation_dashboard:app --host 0.0.0.0 --port 3001
```

## ✅ Verification Checklist

After setup, verify:
- ✅ Dashboard loads at http://localhost:3001
- ✅ Health check returns "healthy" status
- ✅ Can login with admin credentials
- ✅ Database has sample data
- ✅ API endpoints respond correctly
- ✅ No API keys visible in browser
- ✅ System connects to Reddit/Bluesky

## 🎉 You're Ready!

Your local system is now:
- ✅ **Fully Functional** - All features working
- ✅ **Secure** - API keys protected
- ✅ **Professional** - Enterprise-grade features
- ✅ **Local** - Runs entirely on your computer
- ✅ **Monitored** - Health checks and metrics

**Access your professional automation system at http://localhost:3001** 🚀
