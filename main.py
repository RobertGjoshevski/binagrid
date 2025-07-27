#!/usr/bin/env python3
"""
Multi-Strategy Trading Bot Launcher
Supports Grid, DCA, and Signal trading strategies with simulation mode.
"""

import sys
import os
import argparse
from datetime import datetime

def print_banner():
    """Print application banner."""
    print("="*60)
    print("🤖 BINAGRID - Multi-Strategy Trading Bot")
    print("="*60)
    print("📊 Strategies: Grid | DCA | Signal")
    print("🔧 Features: Real Trading | Paper Trading | Analysis")
    print("="*60)

def validate_environment():
    """Validate environment setup."""
    print("🔍 Validating environment...")
    
    # Check if .env file exists
    env_path = os.path.join('common', '.env')
    if not os.path.exists(env_path):
        print("❌ .env file not found in common/ directory")
        print("💡 Please copy common/env_example.txt to common/.env and add your API keys")
        return False
    
    # Check if required packages are installed
    try:
        import binance
        import pandas
        import numpy
        import dotenv
        print("✅ Required packages are installed")
    except ImportError as e:
        print(f"❌ Missing required package: {e}")
        print("💡 Run: cd common && pip install -r requirements.txt")
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

def run_simulation_mode():
    """Run bot in simulation mode."""
    print("🎮 Starting Simulation Mode...")
    
    # Add common to path
    sys.path.append('common')
    
    try:
        from simulation import SimulationManager
        print("✅ Simulation module loaded successfully")
        
        # Get simulation name
        sim_name = input("Enter simulation name (default: 'test_sim'): ").strip()
        if not sim_name:
            sim_name = "test_sim"
        
        # Initialize simulation manager
        sim_manager = SimulationManager(sim_name)
        
        print(f"🎯 Simulation '{sim_name}' initialized with ${sim_manager.initial_balance:,.2f}")
        print("💡 The bot will run in paper trading mode - no real trades will be executed")
        
        # Ask which strategy to run
        print("\nSelect strategy for simulation:")
        print("1. Grid Trading Bot")
        print("2. DCA Trading Bot")
        print("3. Signal Trading Bot")
        
        choice = input("Enter choice (1-3): ").strip()
        
        if choice == '1':
            return run_grid_bot_simulation(sim_manager)
        elif choice == '2':
            return run_dca_bot_simulation(sim_manager)
        elif choice == '3':
            return run_signal_bot_simulation(sim_manager)
        else:
            print("❌ Invalid choice")
            return False
            
    except ImportError as e:
        print(f"❌ Failed to import simulation module: {e}")
        return False
    except Exception as e:
        print(f"❌ Simulation error: {e}")
        return False

def run_grid_bot_simulation(sim_manager):
    """Run Grid Bot in simulation mode."""
    print("🎮 Running Grid Bot in simulation mode...")
    sys.path.append('strategies/grid_bot')
    
    try:
        from grid_bot import GridTradingBot
        from grid_config import GridConfig
        
        # Create bot instance with simulation manager
        bot = GridTradingBot(simulation_manager=sim_manager)
        
        # Run simulation for a limited time
        print("⏱️  Running simulation for 1 hour...")
        import time
        start_time = time.time()
        
        while time.time() - start_time < 3600:  # 1 hour
            bot.run_iteration()
            time.sleep(5)  # 5 second intervals
        
        # Print simulation summary
        sim_manager.print_summary()
        
        # Export results
        sim_manager.export_to_csv()
        sim_manager.export_summary_to_json()
        
        print("✅ Simulation completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Grid Bot simulation error: {e}")
        return False

def run_dca_bot_simulation(sim_manager):
    """Run DCA Bot in simulation mode."""
    print("🎮 Running DCA Bot in simulation mode...")
    # Similar implementation for DCA bot
    print("⚠️  DCA Bot simulation not yet implemented")
    return False

def run_signal_bot_simulation(sim_manager):
    """Run Signal Bot in simulation mode."""
    print("🎮 Running Signal Bot in simulation mode...")
    # Similar implementation for Signal bot
    print("⚠️  Signal Bot simulation not yet implemented")
    return False

def analyze_simulation_results():
    """Analyze simulation results."""
    print("📊 Simulation Analysis Tool")
    
    try:
        from analysis_tool import SimulationAnalyzer
        
        # Get simulation name
        sim_name = input("Enter simulation name to analyze: ").strip()
        if not sim_name:
            print("❌ Please provide a simulation name")
            return False
        
        analyzer = SimulationAnalyzer(sim_name)
        
        print("\nSelect analysis type:")
        print("1. Summary Report")
        print("2. Generate Charts")
        print("3. Export CSV Report")
        print("4. Compare Simulations")
        
        choice = input("Enter choice (1-4): ").strip()
        
        if choice == '1':
            analyzer.print_detailed_analysis()
        elif choice == '2':
            analyzer.plot_pnl_over_time()
            analyzer.plot_trade_distribution()
            analyzer.plot_hourly_performance()
        elif choice == '3':
            analyzer.generate_csv_report()
        elif choice == '4':
            other_sim = input("Enter other simulation name to compare: ").strip()
            if other_sim:
                analyzer.compare_simulations(other_sim)
            else:
                print("❌ Please provide simulation name to compare")
        else:
            print("❌ Invalid choice")
            return False
        
        return True
        
    except ImportError as e:
        print(f"❌ Failed to import analysis tool: {e}")
        return False
    except Exception as e:
        print(f"❌ Analysis error: {e}")
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
        print("4. Run in Simulation Mode")
        print("5. Analyze Simulation Results")
        print("6. Exit")
        
        try:
            choice = input("\nEnter your choice (1-6): ").strip()
            
            if choice == '1':
                return run_grid_bot()
            elif choice == '2':
                return run_dca_bot()
            elif choice == '3':
                return run_signal_bot()
            elif choice == '4':
                return run_simulation_mode()
            elif choice == '5':
                return analyze_simulation_results()
            elif choice == '6':
                print("👋 Goodbye!")
                return True
            else:
                print("❌ Invalid choice. Please enter 1-6.")
                
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
    parser.add_argument('--simulation', '--sim',
                       help='Run in simulation mode with specified name')
    parser.add_argument('--analyze', '-a',
                       help='Analyze simulation results')
    
    args = parser.parse_args()
    
    if args.validate:
        print("🔍 Validating environment...")
        success = validate_environment()
        sys.exit(0 if success else 1)
    
    if args.simulation:
        # Simulation mode
        if not validate_environment():
            sys.exit(1)
        
        # Set up simulation
        sys.path.append('common')
        from simulation import SimulationManager
        sim_manager = SimulationManager(args.simulation)
        
        # Run simulation (simplified for command line)
        print(f"🎮 Running simulation: {args.simulation}")
        print("⚠️  Command line simulation mode is limited. Use interactive mode for full features.")
        sys.exit(0)
    
    if args.analyze:
        # Analysis mode
        from analysis_tool import SimulationAnalyzer
        analyzer = SimulationAnalyzer(args.analyze)
        analyzer.print_detailed_analysis()
        sys.exit(0)
    
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