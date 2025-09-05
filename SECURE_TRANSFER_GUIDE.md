# 🔐 Secure Code Transfer Guide - Moving to Another Computer

## ⚠️ SECURITY FIRST - NO API KEYS IN CODE

### **What to Transfer (Code Only):**
```
Xeinst Ambasdor Automation/
├── moderation_dashboard.py          # Main dashboard application
├── moderation_worker.py             # Background worker
├── create_sample_data.py            # Database initialization
├── bluesky_client.py                # Bluesky integration
├── requirements_moderation.txt      # Python dependencies
├── env.moderation.example           # Environment template (NO KEYS)
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
│   ├── env.example                  # Environment template (NO KEYS)
│   └── prompts/                     # AI prompts
│       ├── system.txt
│       ├── reply_example_automation.txt
│       └── reply_example_entrepreneur.txt
├── README.md                        # Main documentation
├── PROFESSIONAL_SYSTEM.md           # Professional features
├── SYSTEM_STATUS_FINAL.md           # Current status
└── .gitignore                       # Git ignore rules
```

### **What NOT to Transfer:**
```
❌ .env files                        # Contains your API keys
❌ xeinst_reddit_bot/data/xeinst_bot.db    # Database (will be recreated)
❌ xeinst_reddit_bot/venv/                 # Virtual environment (will be recreated)
❌ __pycache__/                            # Python cache files
❌ logs/                                   # Log files (will be recreated)
❌ Any files with actual API keys
```

## 🔐 Secure Setup on New Computer

### **Step 1: Copy Code Files Only**
Copy all the code files listed above to the new computer. **DO NOT copy any .env files or database files.**

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

### **Step 4: Create Environment Files (SECURE)**
```bash
# Copy environment templates (these have NO real keys)
cp env.moderation.example .env
cp xeinst_reddit_bot/env.example xeinst_reddit_bot/.env
```

### **Step 5: Add Your API Keys (SECURELY)**
**Edit the .env files and add YOUR actual API keys:**

**Main .env file:**
```bash
# Reddit API (add your real keys)
REDDIT_CLIENT_ID=your_actual_reddit_client_id
REDDIT_CLIENT_SECRET=your_actual_reddit_client_secret
REDDIT_USERNAME=your_actual_reddit_username
REDDIT_PASSWORD=your_actual_reddit_password

# Bluesky API (add your real keys)
BLUESKY_IDENTIFIER=your_actual_bluesky_handle
BLUESKY_PASSWORD=your_actual_bluesky_password
BLUESKY_SERVICE_URL=https://bsky.social

# Dashboard (add your secure password)
DASHBOARD_USERNAME=admin
DASHBOARD_PASSWORD=your_actual_secure_password

# AI/LLM (add your real keys if using)
OPENAI_API_KEY=your_actual_openai_key
OLLAMA_BASE_URL=http://localhost:11434
```

### **Step 6: Initialize Database**
```bash
# Create sample data and initialize database
python create_sample_data.py
```

### **Step 7: Start the System**
```bash
# Start the professional dashboard
source xeinst_reddit_bot/venv/bin/activate
uvicorn moderation_dashboard:app --host 0.0.0.0 --port 3001
```

## 🛡️ Security Checklist

### **Before Transfer:**
- ✅ Remove any .env files from transfer
- ✅ Remove database files from transfer
- ✅ Remove virtual environment from transfer
- ✅ Remove log files from transfer
- ✅ Check that no API keys are in code files

### **After Transfer:**
- ✅ Create new .env files from templates
- ✅ Add your actual API keys to .env files
- ✅ Set secure passwords
- ✅ Test that system works with your credentials
- ✅ Verify no API keys are exposed in logs

## 🔒 API Key Sources

You'll need to get your API keys from:

### **Reddit API:**
1. Go to https://www.reddit.com/prefs/apps
2. Create a new app
3. Get Client ID and Client Secret

### **Bluesky API:**
1. Go to https://bsky.app
2. Create account
3. Get your handle and app password

### **OpenAI API (if using):**
1. Go to https://platform.openai.com/api-keys
2. Create new API key

## 🚀 Quick Start Commands

```bash
# 1. Copy code files (NO .env files)
# 2. Create virtual environment
python3 -m venv xeinst_reddit_bot/venv
source xeinst_reddit_bot/venv/bin/activate

# 3. Install dependencies
pip install -r requirements_moderation.txt
pip install -r xeinst_reddit_bot/requirements.txt

# 4. Create environment files
cp env.moderation.example .env
cp xeinst_reddit_bot/env.example xeinst_reddit_bot/.env

# 5. Edit .env files with YOUR API keys (not shown here for security)

# 6. Initialize database
python create_sample_data.py

# 7. Start system
uvicorn moderation_dashboard:app --host 0.0.0.0 --port 3001
```

## ✅ Verification

After setup, verify:
- ✅ Dashboard loads at http://localhost:3001
- ✅ Health check works: http://localhost:3001/api/health
- ✅ No API keys visible in browser or logs
- ✅ System connects to Reddit/Bluesky with your credentials

**Your API keys stay secure and private!** 🔐
