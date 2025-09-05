#!/usr/bin/env python3
"""
Start the Xeinst Moderation Dashboard with sample data
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    print("🚀 Starting Xeinst Moderation Dashboard")
    print("=" * 40)
    
    # Ensure we're in the right directory
    if not Path("moderation_dashboard.py").exists():
        print("❌ Error: Please run this script from the project root directory")
        sys.exit(1)
    
    # Create sample data first
    print("📝 Creating sample data...")
    try:
        import create_sample_data
        create_sample_data.create_sample_data()
        print("✅ Sample data created successfully")
    except Exception as e:
        print(f"⚠️ Warning: Could not create sample data: {e}")
    
    # Check if virtual environment exists
    venv_path = Path("xeinst_reddit_bot/venv")
    if venv_path.exists():
        print("🐍 Using existing virtual environment...")
        python_cmd = str(venv_path / "bin" / "python")
    else:
        print("🐍 Using system Python...")
        python_cmd = "python3"
    
    # Start the dashboard
    print("🌐 Starting moderation dashboard...")
    print("📊 Dashboard will be available at: http://localhost:3001")
    print("👤 Username: admin")
    print("🔑 Password: your_secure_password_here (from .env file)")
    print("")
    print("Press Ctrl+C to stop the dashboard")
    print("=" * 40)
    
    try:
        # Start the dashboard
        subprocess.run([python_cmd, "moderation_dashboard.py"], check=True)
    except KeyboardInterrupt:
        print("\n👋 Dashboard stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error starting dashboard: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print("❌ Error: Python not found. Please install Python 3.8+")
        sys.exit(1)

if __name__ == "__main__":
    main()
