#!/usr/bin/env python3
"""
Main launcher for the Multi-Strategy Trading Bot.
Allows users to choose between different trading strategies.
"""

import sys
import os
import argparse
from typing import Dict, Any

def print_banner():
    """Print the application banner."""
    print("=" * 60)
    print("🤖 MULTI-STRATEGY TRADING BOT")
    print("=" * 60)
    print("Available Strategies:")
    print("1. Grid Trading Bot")
    print("2. DCA (Dollar Cost Averaging) Bot")
    print("3. Signal Trading Bot")
    print("=" * 60)

def validate_environment():
    """Validate that the environment is properly set up."""
    # Check if .env file exists
    env_path = os.path.join('common', '.env')
    if not os.path.exists(env_path):
        print("❌ ERROR: .env file not found in common/ directory")
        print("Please copy env_example.txt to common/.env and configure your API keys")
        return False
    
    # Check if common modules exist
    required_files = [
        'common/config.py',
        'common/utils.py',
        'strategies/grid_bot/grid_bot.py',
        'strategies/dca_bot/dca_bot.py',
        'strategies/signal_bot/signal_bot.py'
    ]
    
    for file_path in required_files:
        if not os.path.exists(file_path):
            print(f"❌ ERROR: Required file not found: {file_path}")
            return False
    
    print("✅ Environment validation passed")
    return True

def run_grid_bot():
    """Run the Grid Trading Bot."""
    print("🚀 Starting Grid Trading Bot...")
    sys.path.append('strategies/grid_bot')
    
    try:
        from grid_bot import main as grid_main
        grid_main()
    except ImportError as e:
        print(f"❌ Failed to import Grid Bot: {e}")
        return False
    except Exception as e:
        print(f"❌ Grid Bot error: {e}")
        return False

def run_dca_bot():
    """Run the DCA Trading Bot."""
    print("🚀 Starting DCA Trading Bot...")
    sys.path.append('strategies/dca_bot')
    
    try:
        from dca_bot import main as dca_main
        dca_main()
    except ImportError as e:
        print(f"❌ Failed to import DCA Bot: {e}")
        return False
    except Exception as e:
        print(f"❌ DCA Bot error: {e}")
        return False

def run_signal_bot():
    """Run the Signal Trading Bot."""
    print("🚀 Starting Signal Trading Bot...")
    sys.path.append('strategies/signal_bot')
    
    try:
        from signal_bot import main as signal_main
        signal_main()
    except ImportError as e:
        print(f"❌ Failed to import Signal Bot: {e}")
        return False
    except Exception as e:
        print(f"❌ Signal Bot error: {e}")
        return False

def interactive_mode():
    """Run in interactive mode."""
    print_banner()
    
    if not validate_environment():
        return False
    
    while True:
        print("\nSelect a strategy to run:")
        print("1. Grid Trading Bot")
        print("2. DCA Trading Bot")
        print("3. Signal Trading Bot")
        print("4. Exit")
        
        try:
            choice = input("\nEnter your choice (1-4): ").strip()
            
            if choice == '1':
                return run_grid_bot()
            elif choice == '2':
                return run_dca_bot()
            elif choice == '3':
                return run_signal_bot()
            elif choice == '4':
                print("👋 Goodbye!")
                return True
            else:
                print("❌ Invalid choice. Please enter 1-4.")
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            return True
        except Exception as e:
            print(f"❌ Error: {e}")

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Multi-Strategy Trading Bot')
    parser.add_argument('--strategy', '-s', 
                       choices=['grid', 'dca', 'signal'],
                       help='Strategy to run (grid, dca, signal)')
    parser.add_argument('--validate', '-v', 
                       action='store_true',
                       help='Validate environment and exit')
    
    args = parser.parse_args()
    
    if args.validate:
        print("🔍 Validating environment...")
        success = validate_environment()
        sys.exit(0 if success else 1)
    
    if args.strategy:
        # Command line mode
        if not validate_environment():
            sys.exit(1)
        
        if args.strategy == 'grid':
            success = run_grid_bot()
        elif args.strategy == 'dca':
            success = run_dca_bot()
        elif args.strategy == 'signal':
            success = run_signal_bot()
        
        sys.exit(0 if success else 1)
    else:
        # Interactive mode
        success = interactive_mode()
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 