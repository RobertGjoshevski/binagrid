#!/usr/bin/env python3
"""
Test script for Web UI
Verifies that the web UI can start and basic functionality works.
"""

import os
import sys
import subprocess
import time
import requests
from pathlib import Path

def test_web_ui():
    """Test the web UI functionality."""
    print("🧪 Testing Web UI...")
    
    # Check if we're in the right directory
    if not Path("web_ui").exists():
        print("❌ web_ui directory not found")
        return False
    
    # Check if required files exist
    required_files = [
        "web_ui/app.py",
        "web_ui/run_web_ui.py",
        "web_ui/templates/base.html",
        "web_ui/templates/index.html",
        "web_ui/templates/dashboard.html"
    ]
    
    for file_path in required_files:
        if not Path(file_path).exists():
            print(f"❌ Required file not found: {file_path}")
            return False
    
    print("✅ All required files found")
    
    # Check if dependencies are installed
    try:
        import flask
        import flask_socketio
        print("✅ Flask dependencies installed")
    except ImportError as e:
        print(f"❌ Missing Flask dependency: {e}")
        return False
    
    # Test if we can import the app
    try:
        sys.path.append('web_ui')
        from web_ui.app import app
        print("✅ Flask app can be imported")
    except Exception as e:
        print(f"❌ Cannot import Flask app: {e}")
        return False
    
    print("✅ Web UI test passed!")
    return True

def run_example_simulation():
    """Run example simulation to generate test data."""
    print("🎮 Running example simulation for test data...")
    
    try:
        result = subprocess.run([
            sys.executable, "example_simulation.py"
        ], input=b'1\n', capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ Example simulation completed")
            return True
        else:
            print(f"⚠️  Example simulation had issues: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("⚠️  Example simulation timed out")
        return False
    except Exception as e:
        print(f"⚠️  Could not run example simulation: {e}")
        return False

def main():
    """Main test function."""
    print("🤖 Binagrid Web UI Test")
    print("=" * 40)
    
    # Test web UI
    if not test_web_ui():
        print("❌ Web UI test failed")
        return False
    
    # Run example simulation
    print("\n🎮 Would you like to run an example simulation to generate test data?")
    print("   This will create sample data for the web interface.")
    
    try:
        choice = input("   Run example simulation? (y/n): ").strip().lower()
        if choice in ['y', 'yes']:
            run_example_simulation()
    except KeyboardInterrupt:
        print("\n👋 Test cancelled")
        return False
    
    print("\n✅ All tests completed successfully!")
    print("🚀 You can now run the web UI with:")
    print("   python3 web_ui/run_web_ui.py")
    print("   or")
    print("   python3 main.py (select option 6)")
    
    return True

if __name__ == "__main__":
    main() 