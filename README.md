# 🎯 Xeinst Ambassador Automation - Reddit & Bluesky

A streamlined automation system for managing content across Reddit and Bluesky platforms with AI-powered moderation and human oversight.

## 🚀 Quick Start

```bash
# Start the system
python start_dashboard.py
```

**Access Dashboard:**
- **URL**: http://localhost:3001
- **Username**: admin
- **Password**: your_secure_password_here

## 📁 Project Structure

```
├── moderation_dashboard.py      # Main web dashboard
├── moderation_worker.py         # Background posting worker
├── bluesky_client.py           # Bluesky API client
├── create_sample_data.py       # Sample data generator
├── start_dashboard.py          # Simple startup script
├── requirements_moderation.txt # Python dependencies
├── env.moderation.example      # Environment configuration
├── templates/
│   └── dashboard.html          # Web interface
└── xeinst_reddit_bot/          # Core Reddit bot
    ├── reddit_client.py        # Reddit API client
    ├── llm.py                  # AI content generation
    ├── moderation.py           # Content moderation
    ├── db.py                   # Database management
    └── config.py               # Configuration
```

## ⚙️ Configuration

1. **Copy environment file:**
   ```bash
   cp env.moderation.example .env
   ```

2. **Edit `.env` with your credentials:**
   ```bash
   # Reddit Configuration
   REDDIT_CLIENT_ID=your_reddit_client_id
   REDDIT_CLIENT_SECRET=your_reddit_client_secret
   REDDIT_USERNAME=your_reddit_username
   REDDIT_PASSWORD=your_reddit_password
   
   # Bluesky Configuration
   BLUESKY_IDENTIFIER=your_bluesky_identifier
   BLUESKY_PASSWORD=your_bluesky_password
   
   # System Settings
   ADMIN_PASSWORD=your_secure_password_here
   ```

3. **Install dependencies:**
   ```bash
   source xeinst_reddit_bot/venv/bin/activate
   pip install -r requirements_moderation.txt
   ```

4. **Create sample data:**
   ```bash
   python create_sample_data.py
   ```

## 🎯 Features

### Dashboard
- **Post Management**: Review, approve, and edit content
- **Platform Filtering**: Separate Reddit and Bluesky posts
- **Bulk Operations**: Approve multiple posts at once
- **Real-time Stats**: Platform-specific statistics
- **Safety Checks**: Similarity detection and policy flags

### Automation
- **AI Content**: Generate posts using local LLM
- **Smart Moderation**: Toxicity filtering and spam detection
- **Rate Limiting**: Respect platform limits
- **Scheduled Posting**: Time-based content publishing
- **Error Handling**: Robust error recovery

### Platforms
- **Reddit**: Full integration with existing bot
- **Bluesky**: AT Protocol client (simulated)
- **Cross-platform**: Unified content management

## 📊 Sample Data

The system includes 8 sample posts:
- **4 Reddit posts**: Automation, no-code, workflow, productivity
- **4 Bluesky posts**: SaaS, marketing, entrepreneurship, test content

## 🔧 Usage

1. **Start Dashboard**: `python start_dashboard.py`
2. **Review Posts**: Visit http://localhost:3001
3. **Approve Content**: Use the web interface
4. **Monitor Activity**: Check logs and statistics

## 🛡️ Safety Features

- **Content Moderation**: AI-powered toxicity detection
- **Similarity Checking**: Prevent duplicate content
- **Rate Limiting**: Respect platform guidelines
- **Human Oversight**: Manual approval required
- **Policy Flags**: Custom content rules

## 📝 Logs

- **Dashboard**: Web interface logs
- **Worker**: Background posting logs
- **Database**: SQLite with full history

## 🚀 Production Ready

- **Environment Variables**: Secure configuration
- **Database**: SQLite for local storage
- **Error Handling**: Comprehensive error recovery
- **Monitoring**: Real-time statistics
- **Scalable**: Easy to extend to more platforms

---

**Ready to automate your Reddit and Bluesky content!** 🎉
