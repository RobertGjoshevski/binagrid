#!/usr/bin/env python3
"""
Web UI Launcher for Binagrid Trading Bot
Provides easy access to the web interface.
"""

import os
import sys
import subprocess
import webbrowser
import time
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed."""
    try:
        import flask
        import flask_socketio
        import pandas
        import numpy
        print("✅ All web dependencies are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("💡 Installing web dependencies...")
        return install_dependencies()

def install_dependencies():
    """Install web UI dependencies."""
    try:
        # Get the path to requirements.txt
        requirements_path = Path(__file__).parent.parent / "common" / "requirements.txt"
        
        if not requirements_path.exists():
            print("❌ requirements.txt not found")
            return False
        
        # Install dependencies
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", str(requirements_path)
        ])
        
        print("✅ Dependencies installed successfully")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def create_simulation_data():
    """Create simulation data directory if it doesn't exist."""
    sim_data_dir = Path(__file__).parent.parent / "simulation_data"
    sim_data_dir.mkdir(exist_ok=True)
    print(f"✅ Simulation data directory: {sim_data_dir}")

def run_example_simulation():
    """Run example simulation to generate sample data."""
    try:
        example_script = Path(__file__).parent.parent / "example_simulation.py"
        
        if example_script.exists():
            print("🎮 Running example simulation to generate sample data...")
            subprocess.run([sys.executable, str(example_script)], 
                         input=b'1\n',  # Choose simple simulation
                         timeout=30)
            print("✅ Example simulation completed")
        else:
            print("⚠️  Example simulation script not found")
            
    except subprocess.TimeoutExpired:
        print("⚠️  Example simulation timed out")
    except Exception as e:
        print(f"⚠️  Could not run example simulation: {e}")

def start_web_server():
    """Start the Flask web server."""
    try:
        # Change to web_ui directory
        web_ui_dir = Path(__file__).parent
        os.chdir(web_ui_dir)
        
        print("🌐 Starting Binagrid Web UI...")
        print("📊 Dashboard will be available at: http://localhost:5000")
        print("🔄 Press Ctrl+C to stop the server")
        print("-" * 50)
        
        # Start the Flask app
        from app import app, socketio
        socketio.run(app, host='0.0.0.0', port=5000, debug=False)
        
    except KeyboardInterrupt:
        print("\n👋 Web UI stopped")
    except Exception as e:
        print(f"❌ Failed to start web server: {e}")

def main():
    """Main function."""
    print("🤖 Binagrid Web UI Launcher")
    print("=" * 40)
    
    # Check and install dependencies
    if not check_dependencies():
        print("❌ Cannot start web UI due to missing dependencies")
        return
    
    # Create simulation data directory
    create_simulation_data()
    
    # Ask if user wants to run example simulation
    print("\n🎮 Would you like to run an example simulation to generate sample data?")
    print("   This will create demo data for the web interface.")
    
    try:
        choice = input("   Run example simulation? (y/n): ").strip().lower()
        if choice in ['y', 'yes']:
            run_example_simulation()
    except KeyboardInterrupt:
        print("\n👋 Cancelled")
        return
    
    # Start web server
    print("\n🚀 Starting web server...")
    time.sleep(1)
    
    # Open browser after a short delay
    def open_browser():
        time.sleep(2)
        try:
            webbrowser.open('http://localhost:5000')
        except:
            pass
    
    import threading
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()
    
    # Start the server
    start_web_server()

if __name__ == "__main__":
    main() 