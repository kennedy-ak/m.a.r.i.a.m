#!/usr/bin/env python3
"""
Startup script for the Personal Assistant Bot
"""
import os
import sys
import subprocess


def main():
    """Main startup function"""
    print("Starting Personal Assistant Bot...")
    
    # Check if we're in the right directory
    if not os.path.exists('app'):
        print("[ERROR] 'app' directory not found. Please run from project root.")
        sys.exit(1)
    
    # Check if virtual environment exists
    if not os.path.exists('env'):
        print("[ERROR] Virtual environment 'env' not found.")
        print("Please create it with: python -m venv env")
        sys.exit(1)
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        print("[ERROR] .env file not found.")
        print("Please copy .env.example to .env and configure it.")
        sys.exit(1)
    
    print("[OK] Environment checks passed")
    
    # Test imports first
    print("\nTesting imports...")
    try:
        result = subprocess.run([
            sys.executable, "test_imports.py"
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print("[ERROR] Import test failed:")
            print(result.stdout)
            print(result.stderr)
            sys.exit(1)
        else:
            print("[OK] All imports successful")
    except Exception as e:
        print(f"[ERROR] Failed to test imports: {e}")
        sys.exit(1)
    
    # Start the main application
    print("\nStarting FastAPI server...")
    try:
        subprocess.run([sys.executable, "main.py"])
    except KeyboardInterrupt:
        print("\n[INFO] Bot stopped by user")
    except Exception as e:
        print(f"[ERROR] Error starting bot: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()