# 🚀 Code Transfer Guide - Moving to Another Computer

## 📦 What You Need to Transfer

### **Essential Files to Copy:**
```
Xeinst Ambasdor Automation/
├── moderation_dashboard.py          # Main dashboard application
├── moderation_worker.py             # Background worker
├── create_sample_data.py            # Database initialization
├── bluesky_client.py                # Bluesky integration
├── requirements_moderation.txt      # Python dependencies
├── env.moderation.example           # Environment template
├── templates/
│   ├── dashboard.html               # Original dashboard
│   └── dashboard_pro.html           # Professional dashboard
├── xeinst_reddit_bot/
│   ├── config.py                    # Configuration
│   ├── db.py                        # Database management
│   ├── moderation.py                # Content moderation
│   ├── reddit_client.py             # Reddit integration
│   ├── llm.py                       # AI integration
│   ├── scheduler.py                 # Task scheduling
│   ├── cli.py                       # Command line interface
│   ├── config.yaml                  # YAML configuration
│   ├── requirements.txt             # Reddit bot dependencies
│   ├── env.example                  # Environment template
│   └── prompts/                     # AI prompts
│       ├── system.txt
│       ├── reply_example_automation.txt
│       └── reply_example_entrepreneur.txt
├── README.md                        # Main documentation
├── PROFESSIONAL_SYSTEM.md           # Professional features
├── SYSTEM_STATUS_FINAL.md           # Current status
└── .gitignore                       # Git ignore rules
```

### **Files NOT to Transfer:**
```
❌ xeinst_reddit_bot/data/xeinst_bot.db    # Database (will be recreated)
❌ xeinst_reddit_bot/venv/                 # Virtual environment (will be recreated)
❌ __pycache__/                            # Python cache files
❌ logs/                                   # Log files (will be recreated)
```

## 🔧 Setup on New Computer

### **Step 1: Copy Files**
Copy all the essential files listed above to the new computer.

### **Step 2: Create Virtual Environment**
```bash
# Navigate to project directory
cd "Xeinst Ambasdor Automation"

# Create virtual environment
python3 -m venv xeinst_reddit_bot/venv

# Activate virtual environment
source xeinst_reddit_bot/venv/bin/activate  # On macOS/Linux
# OR
xeinst_reddit_bot/venv/Scripts/activate     # On Windows
```

### **Step 3: Install Dependencies**
```bash
# Install moderation system dependencies
pip install -r requirements_moderation.txt

# Install Reddit bot dependencies
pip install -r xeinst_reddit_bot/requirements.txt
```

### **Step 4: Set Up Environment Variables**
```bash
# Copy environment template
cp env.moderation.example .env

# Edit .env file with your credentials
nano .env  # or use your preferred editor
```

**Required Environment Variables:**
```bash
# Reddit API
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
REDDIT_USERNAME=your_reddit_username
REDDIT_PASSWORD=your_reddit_password

# Bluesky API
BLUESKY_IDENTIFIER=your_bluesky_handle
BLUESKY_PASSWORD=your_bluesky_password
BLUESKY_SERVICE_URL=https://bsky.social

# Dashboard
DASHBOARD_USERNAME=admin
DASHBOARD_PASSWORD=your_secure_password_here

# AI/LLM (if using)
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
source xeinst_reddit_bot/venv/bin/activate
uvicorn moderation_dashboard:app --host 0.0.0.0 --port 3001
```

## 🎯 Quick Transfer Script

Let me create a script to help with the transfer:
