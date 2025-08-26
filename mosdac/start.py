#!/usr/bin/env python3
"""
Startup script for MOSDAC AI Help Bot
"""

import os
import sys
import subprocess
import time
import signal
import threading
from pathlib import Path

def print_banner():
    """Print startup banner"""
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║                    🚀 MOSDAC AI Help Bot                    ║
    ║                                                              ║
    ║    AI-based Help Bot for Information Retrieval from         ║
    ║    MOSDAC Portal using Knowledge Graphs and NLP/ML          ║
    ║                                                              ║
    ║    Version: 1.0.0                                           ║
    ║    Built with ❤️ for MOSDAC Portal                          ║
    ╚══════════════════════════════════════════════════════════════╝
    """)

def check_dependencies():
    """Check if required dependencies are installed"""
    print("🔍 Checking dependencies...")
    
    required_packages = [
        "fastapi", "uvicorn", "streamlit", "requests",
        "beautifulsoup4", "selenium", "spacy", "sentence_transformers"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
            print(f"  ✅ {package}")
        except ImportError:
            print(f"  ❌ {package} - NOT INSTALLED")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n❌ Missing packages: {', '.join(missing_packages)}")
        print("Please install missing packages using:")
        print("pip install -r requirements.txt")
        return False
    
    print("✅ All dependencies are installed!")
    return True

def check_environment():
    """Check environment configuration"""
    print("\n🔧 Checking environment configuration...")
    
    env_file = Path(".env")
    if not env_file.exists():
        print("⚠️  .env file not found. Creating from template...")
        
        # Copy from env.example if it exists
        example_file = Path("env.example")
        if example_file.exists():
            import shutil
            shutil.copy(example_file, env_file)
            print("✅ Created .env file from template")
            print("⚠️  Please edit .env file with your configuration values")
            return False
        else:
            print("❌ env.example file not found")
            return False
    
    print("✅ .env file found")
    
    # Check for required environment variables
    required_vars = ["OPENAI_API_KEY"]
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"⚠️  Missing environment variables: {', '.join(missing_vars)}")
        print("Please set these variables in your .env file")
        return False
    
    print("✅ Environment configuration is complete")
    return True

def start_backend():
    """Start the FastAPI backend"""
    print("\n🚀 Starting FastAPI backend...")
    
    backend_dir = Path("src/api")
    if not backend_dir.exists():
        print("❌ Backend directory not found")
        return None
    
    try:
        # Change to backend directory
        os.chdir(backend_dir)
        
        # Start uvicorn server
        process = subprocess.Popen([
            sys.executable, "-m", "uvicorn", "main:app",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--reload"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait a bit for server to start
        time.sleep(3)
        
        # Check if server is running
        try:
            import requests
            response = requests.get("http://localhost:8000/health", timeout=5)
            if response.status_code == 200:
                print("✅ Backend started successfully on http://localhost:8000")
                return process
            else:
                print("❌ Backend health check failed")
                return None
        except:
            print("❌ Backend is not responding")
            return None
            
    except Exception as e:
        print(f"❌ Failed to start backend: {e}")
        return None

def start_frontend():
    """Start the Streamlit frontend"""
    print("\n🌐 Starting Streamlit frontend...")
    
    frontend_dir = Path("src/web")
    if not frontend_dir.exists():
        print("❌ Frontend directory not found")
        return None
    
    try:
        # Change to frontend directory
        os.chdir(frontend_dir)
        
        # Start streamlit
        process = subprocess.Popen([
            sys.executable, "-m", "streamlit", "run", "app.py",
            "--server.port", "8501",
            "--server.address", "localhost"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait a bit for server to start
        time.sleep(5)
        
        print("✅ Frontend started successfully on http://localhost:8501")
        return process
        
    except Exception as e:
        print(f"❌ Failed to start frontend: {e}")
        return None

def run_tests():
    """Run basic tests"""
    print("\n🧪 Running basic tests...")
    
    try:
        # Change back to project root
        os.chdir(Path(__file__).parent)
        
        # Run test script
        result = subprocess.run([
            sys.executable, "test_bot.py"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Tests passed!")
        else:
            print("⚠️  Some tests failed")
            print("Test output:")
            print(result.stdout)
            if result.stderr:
                print("Test errors:")
                print(result.stderr)
                
    except Exception as e:
        print(f"❌ Failed to run tests: {e}")

def main():
    """Main startup function"""
    
    # Print banner
    print_banner()
    
    # Check dependencies
    if not check_dependencies():
        print("\n❌ Dependency check failed. Please install missing packages.")
        return
    
    # Check environment
    if not check_environment():
        print("\n❌ Environment configuration incomplete.")
        print("Please configure your .env file and try again.")
        return
    
    # Store original directory
    original_dir = os.getcwd()
    
    # Start backend
    backend_process = start_backend()
    if not backend_process:
        print("\n❌ Failed to start backend. Exiting.")
        return
    
    # Start frontend
    frontend_process = start_frontend()
    if not frontend_process:
        print("\n❌ Failed to start frontend. Exiting.")
        backend_process.terminate()
        return
    
    # Change back to original directory
    os.chdir(original_dir)
    
    print("\n🎉 MOSDAC AI Help Bot is now running!")
    print("\n📱 Access Points:")
    print("  • Backend API: http://localhost:8000")
    print("  • API Docs: http://localhost:8000/docs")
    print("  • Web Interface: http://localhost:8501")
    
    print("\n🔧 Management:")
    print("  • Press Ctrl+C to stop all services")
    print("  • Run 'python test_bot.py' to test functionality")
    print("  • Check logs in the logs/ directory")
    
    # Run tests in background
    test_thread = threading.Thread(target=run_tests)
    test_thread.daemon = True
    test_thread.start()
    
    try:
        # Keep running until interrupted
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down services...")
        
        # Stop frontend
        if frontend_process:
            frontend_process.terminate()
            print("✅ Frontend stopped")
        
        # Stop backend
        if backend_process:
            backend_process.terminate()
            print("✅ Backend stopped")
        
        print("👋 Goodbye!")

if __name__ == "__main__":
    main()
