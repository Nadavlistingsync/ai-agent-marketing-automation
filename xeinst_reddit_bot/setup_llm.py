#!/usr/bin/env python3
"""
LLM Setup Script for Xeinst Reddit Bot
Downloads Ollama, pulls Llama3 model, and sets up everything needed
"""

import os
import sys
import subprocess
import platform
import requests
import time
from pathlib import Path

def print_status(message, status="ℹ️"):
    """Print a status message with emoji"""
    print(f"{status} {message}")

def check_command(command):
    """Check if a command exists"""
    try:
        subprocess.run([command, "--version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def get_system_info():
    """Get system information for Ollama installation"""
    system = platform.system().lower()
    machine = platform.machine().lower()
    
    if system == "darwin":  # macOS
        if "arm" in machine or "aarch64" in machine:
            return "macos-arm64"
        else:
            return "macos-amd64"
    elif system == "linux":
        if "arm" in machine or "aarch64" in machine:
            return "linux-arm64"
        else:
            return "linux-amd64"
    elif system == "windows":
        return "windows-amd64"
    else:
        return "linux-amd64"  # Default fallback

def install_ollama():
    """Install Ollama based on the system"""
    print_status("Installing Ollama...", "🚀")
    
    system_type = get_system_info()
    print_status(f"Detected system: {system_type}")
    
    if system_type == "macos-arm64" or system_type == "macos-amd64":
        # macOS installation
        try:
            print_status("Installing Ollama on macOS...")
            result = subprocess.run([
                "curl", "-fsSL", "https://ollama.ai/install.sh"
            ], capture_output=True, text=True, check=True)
            
            install_script = result.stdout
            # Execute the install script
            subprocess.run(["bash", "-c", install_script], check=True)
            print_status("✅ Ollama installed successfully on macOS")
            return True
            
        except subprocess.CalledProcessError as e:
            print_status(f"❌ Failed to install Ollama on macOS: {e}", "❌")
            return False
    
    elif system_type == "linux-arm64" or system_type == "linux-amd64":
        # Linux installation
        try:
            print_status("Installing Ollama on Linux...")
            result = subprocess.run([
                "curl", "-fsSL", "https://ollama.ai/install.sh"
            ], capture_output=True, text=True, check=True)
            
            install_script = result.stdout
            # Execute the install script
            subprocess.run(["bash", "-c", install_script], check=True)
            print_status("✅ Ollama installed successfully on Linux")
            return True
            
        except subprocess.CalledProcessError as e:
            print_status(f"❌ Failed to install Ollama on Linux: {e}", "❌")
            return False
    
    elif system_type == "windows-amd64":
        # Windows installation
        print_status("For Windows, please download Ollama from: https://ollama.ai/download")
        print_status("After downloading, run: ollama serve")
        return False
    
    else:
        print_status(f"❌ Unsupported system: {system_type}", "❌")
        return False

def start_ollama_service():
    """Start the Ollama service"""
    print_status("Starting Ollama service...", "🔄")
    
    try:
        # Check if Ollama is already running
        try:
            response = requests.get('http://localhost:11434/api/tags', timeout=5)
            if response.status_code == 200:
                print_status("✅ Ollama is already running")
                return True
        except:
            pass
        
        # Start Ollama in the background
        print_status("Starting Ollama service in background...")
        
        if platform.system().lower() == "windows":
            # Windows
            subprocess.Popen(["ollama", "serve"], 
                           creationflags=subprocess.CREATE_NEW_CONSOLE)
        else:
            # macOS/Linux
            subprocess.Popen(["ollama", "serve"], 
                           stdout=subprocess.DEVNULL, 
                           stderr=subprocess.DEVNULL)
        
        # Wait for Ollama to start
        print_status("Waiting for Ollama to start...")
        for i in range(30):  # Wait up to 30 seconds
            try:
                response = requests.get('http://localhost:11434/api/tags', timeout=5)
                if response.status_code == 200:
                    print_status("✅ Ollama service started successfully")
                    return True
            except:
                pass
            time.sleep(1)
            if (i + 1) % 5 == 0:
                print_status(f"Still waiting... ({i + 1}/30 seconds)")
        
        print_status("❌ Ollama service failed to start within 30 seconds", "❌")
        return False
        
    except Exception as e:
        print_status(f"❌ Failed to start Ollama service: {e}", "❌")
        return False

def pull_llama3_model():
    """Pull the Llama3 model"""
    print_status("Pulling Llama3 model...", "📥")
    
    try:
        # Check if model already exists
        try:
            response = requests.get('http://localhost:11434/api/tags', timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                if any('llama3' in model.get('name', '') for model in models):
                    print_status("✅ Llama3 model already exists")
                    return True
        except:
            pass
        
        print_status("Downloading Llama3 model (this may take 10-30 minutes)...")
        print_status("Model size: ~4GB")
        
        # Pull the model
        result = subprocess.run([
            "ollama", "pull", "llama3"
        ], capture_output=True, text=True, check=True)
        
        print_status("✅ Llama3 model downloaded successfully")
        return True
        
    except subprocess.CalledProcessError as e:
        print_status(f"❌ Failed to pull Llama3 model: {e}", "❌")
        print_status(f"Error output: {e.stderr}")
        return False
    except Exception as e:
        print_status(f"❌ Unexpected error pulling model: {e}", "❌")
        return False

def test_ollama_connection():
    """Test the Ollama connection"""
    print_status("Testing Ollama connection...", "🧪")
    
    try:
        response = requests.get('http://localhost:11434/api/tags', timeout=10)
        if response.status_code == 200:
            models = response.json().get('models', [])
            print_status(f"✅ Connected to Ollama successfully")
            print_status(f"Available models: {[model.get('name', 'unknown') for model in models]}")
            return True
        else:
            print_status(f"❌ Ollama API returned status {response.status_code}", "❌")
            return False
    except Exception as e:
        print_status(f"❌ Failed to connect to Ollama: {e}", "❌")
        return False

def test_llama3_generation():
    """Test Llama3 model generation"""
    print_status("Testing Llama3 model generation...", "🧪")
    
    try:
        # Simple test prompt
        test_payload = {
            "model": "llama3",
            "prompt": "Hello, how are you?",
            "stream": False
        }
        
        response = requests.post(
            'http://localhost:11434/api/generate',
            json=test_payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            generated_text = result.get('response', '').strip()
            print_status("✅ Llama3 model generation test successful")
            print_status(f"Generated text: {generated_text[:100]}...")
            return True
        else:
            print_status(f"❌ Model generation failed with status {response.status_code}", "❌")
            return False
            
    except Exception as e:
        print_status(f"❌ Model generation test failed: {e}", "❌")
        return False

def setup_python_dependencies():
    """Install Python dependencies"""
    print_status("Installing Python dependencies...", "🐍")
    
    try:
        requirements_file = Path("requirements.txt")
        if requirements_file.exists():
            subprocess.run([
                sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
            ], check=True)
            print_status("✅ Python dependencies installed successfully")
            return True
        else:
            print_status("⚠️ requirements.txt not found, skipping Python dependency installation", "⚠️")
            return True
    except subprocess.CalledProcessError as e:
        print_status(f"❌ Failed to install Python dependencies: {e}", "❌")
        return False

def create_directories():
    """Create necessary directories"""
    print_status("Creating necessary directories...", "📁")
    
    directories = ['data', 'logs']
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print_status(f"    ✅ {directory}/")
    
    return True

def show_next_steps():
    """Show next steps for the user"""
    print("\n🎉 LLM Setup Complete!")
    print("=" * 50)
    print("\n🎯 Next Steps:")
    print("1. Configure your Reddit credentials:")
    print("   cp env.example .env")
    print("   # Edit .env with your Reddit API credentials")
    print("\n2. Seed the database:")
    print("   make seed")
    print("\n3. Start the bot:")
    print("   make dev")
    print("   # Or manually: python scheduler.py")
    print("\n4. Monitor the queue:")
    print("   python cli.py queue:list")
    print("\n📚 For more help:")
    print("   - make help          # Show all available commands")
    print("   - python cli.py --help  # Show CLI help")
    print("   - README.md          # Full documentation")

def main():
    """Main setup function"""
    print("🚀 Xeinst Reddit Bot - LLM Setup")
    print("=" * 50)
    print("This script will:")
    print("1. Install Ollama (if not already installed)")
    print("2. Start Ollama service")
    print("3. Download Llama3 model (~4GB)")
    print("4. Test the setup")
    print("5. Install Python dependencies")
    print("=" * 50)
    
    # Check if Ollama is already installed
    if check_command("ollama"):
        print_status("✅ Ollama is already installed")
    else:
        print_status("Ollama not found, installing...")
        if not install_ollama():
            print_status("❌ Ollama installation failed. Please install manually from https://ollama.ai", "❌")
            return
    
    # Start Ollama service
    if not start_ollama_service():
        print_status("❌ Failed to start Ollama service", "❌")
        return
    
    # Pull Llama3 model
    if not pull_llama3_model():
        print_status("❌ Failed to pull Llama3 model", "❌")
        return
    
    # Test connection
    if not test_ollama_connection():
        print_status("❌ Failed to connect to Ollama", "❌")
        return
    
    # Test model generation
    if not test_llama3_generation():
        print_status("❌ Failed to test model generation", "❌")
        return
    
    # Setup Python dependencies
    setup_python_dependencies()
    
    # Create directories
    create_directories()
    
    # Show next steps
    show_next_steps()

if __name__ == "__main__":
    main()
