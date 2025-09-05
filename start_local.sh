#!/bin/bash

echo "🚀 Starting Xeinst Ambassador Automation (Local)"
echo "================================================"

# Check if virtual environment exists
if [ ! -d "xeinst_reddit_bot/venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Please run setup first:"
    echo "1. python3 -m venv xeinst_reddit_bot/venv"
    echo "2. source xeinst_reddit_bot/venv/bin/activate"
    echo "3. pip install -r requirements_moderation.txt"
    echo "4. pip install -r xeinst_reddit_bot/requirements.txt"
    exit 1
fi

# Activate virtual environment
echo "🐍 Activating virtual environment..."
source xeinst_reddit_bot/venv/bin/activate

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found!"
    echo "Please create .env file from template:"
    echo "cp env.moderation.example .env"
    echo "Then edit .env with your API keys"
    exit 1
fi

# Check if database exists
if [ ! -f "xeinst_reddit_bot/data/xeinst_bot.db" ]; then
    echo "📊 Initializing database..."
    python create_sample_data.py
fi

# Start dashboard
echo "🌐 Starting professional dashboard..."
echo "📊 Dashboard will be available at: http://localhost:3001"
echo "🔑 Username: admin"
echo "🔐 Password: (check your .env file)"
echo ""
echo "Press Ctrl+C to stop the dashboard"
echo "================================================"

uvicorn moderation_dashboard:app --host 0.0.0.0 --port 3001
