@echo off
echo 🚀 Starting Xeinst Ambassador Automation (Local)
echo ================================================

REM Check if virtual environment exists
if not exist "xeinst_reddit_bot\venv" (
    echo ❌ Virtual environment not found!
    echo Please run setup first:
    echo 1. python -m venv xeinst_reddit_bot\venv
    echo 2. xeinst_reddit_bot\venv\Scripts\activate
    echo 3. pip install -r requirements_moderation.txt
    echo 4. pip install -r xeinst_reddit_bot\requirements.txt
    pause
    exit /b 1
)

REM Activate virtual environment
echo 🐍 Activating virtual environment...
call xeinst_reddit_bot\venv\Scripts\activate

REM Check if .env file exists
if not exist ".env" (
    echo ❌ .env file not found!
    echo Please create .env file from template:
    echo copy env.moderation.example .env
    echo Then edit .env with your API keys
    pause
    exit /b 1
)

REM Check if database exists
if not exist "xeinst_reddit_bot\data\xeinst_bot.db" (
    echo 📊 Initializing database...
    python create_sample_data.py
)

REM Start dashboard
echo 🌐 Starting professional dashboard...
echo 📊 Dashboard will be available at: http://localhost:3001
echo 🔑 Username: admin
echo 🔐 Password: (check your .env file)
echo.
echo Press Ctrl+C to stop the dashboard
echo ================================================

uvicorn moderation_dashboard:app --host 0.0.0.0 --port 3001
