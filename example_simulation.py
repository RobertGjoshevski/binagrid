#!/usr/bin/env python3
"""
Example Simulation Script
Demonstrates how to use the simulation system with sample trades.
"""

import sys
import os
import time
from datetime import datetime, timedelta
import uuid

# Add common to path
sys.path.append('common')
from simulation import SimulationManager, Trade

def create_sample_trades():
    """Create sample trades for demonstration."""
    trades = []
    
    # Sample data
    base_price = 50000.0  # BTC price
    base_time = int(datetime.now().timestamp())
    
    # Trade 1: Buy BTC
    trades.append(Trade(
        id=str(uuid.uuid4()),
        timestamp=base_time,
        symbol="BTCUSDT",
        side="BUY",
        quantity=0.1,
        price=base_price,
        total_value=5000.0,
        strategy="GRID",
        reason="Grid buy order",
        order_id="order_001",
        commission=5.0
    ))
    
    # Trade 2: Sell BTC (profit)
    trades.append(Trade(
        id=str(uuid.uuid4()),
        timestamp=base_time + 3600,  # 1 hour later
        symbol="BTCUSDT",
        side="SELL",
        quantity=0.05,
        price=base_price * 1.02,  # 2% profit
        total_value=2550.0,
        strategy="GRID",
        reason="Grid sell order",
        order_id="order_002",
        commission=2.55
    ))
    
    # Trade 3: Buy more BTC
    trades.append(Trade(
        id=str(uuid.uuid4()),
        timestamp=base_time + 7200,  # 2 hours later
        symbol="BTCUSDT",
        side="BUY",
        quantity=0.08,
        price=base_price * 0.98,  # 2% dip
        total_value=3920.0,
        strategy="DCA",
        reason="DCA dip buying",
        order_id="order_003",
        commission=3.92
    ))
    
    # Trade 4: Sell BTC (loss)
    trades.append(Trade(
        id=str(uuid.uuid4()),
        timestamp=base_time + 10800,  # 3 hours later
        symbol="BTCUSDT",
        side="SELL",
        quantity=0.03,
        price=base_price * 0.97,  # 3% loss
        total_value=1455.0,
        strategy="GRID",
        reason="Grid sell order",
        order_id="order_004",
        commission=1.46
    ))
    
    return trades

def run_sample_simulation():
    """Run a sample simulation with demo data."""
    print("🎮 Running Sample Simulation...")
    
    # Create simulation manager
    sim_name = "demo_simulation"
    sim_manager = SimulationManager(sim_name)
    
    print(f"✅ Created simulation: {sim_name}")
    print(f"💰 Starting balance: ${sim_manager.initial_balance:,.2f}")
    
    # Create and execute sample trades
    sample_trades = create_sample_trades()
    
    print(f"\n📊 Executing {len(sample_trades)} sample trades...")
    
    for i, trade in enumerate(sample_trades, 1):
        print(f"  Trade {i}: {trade.side} {trade.quantity} {trade.symbol} @ ${trade.price:,.2f}")
        
        # Execute trade
        success = sim_manager.execute_trade(trade)
        
        if success:
            print(f"    ✅ Executed successfully")
            print(f"    💰 Current balance: ${sim_manager.current_balance:,.2f}")
        else:
            print(f"    ❌ Failed to execute")
        
        print()
    
    # Print final summary
    print("📊 SIMULATION COMPLETED")
    print("="*50)
    sim_manager.print_summary()
    
    # Export results
    print("\n📄 Exporting results...")
    sim_manager.export_to_csv()
    sim_manager.export_summary_to_json()
    
    print(f"✅ Results exported to simulation_data/{sim_name}_*")
    
    return sim_manager

def run_backtest_simulation():
    """Run a more realistic backtest simulation."""
    print("📈 Running Backtest Simulation...")
    
    # Create simulation manager
    sim_name = "backtest_simulation"
    sim_manager = SimulationManager(sim_name)
    
    print(f"✅ Created simulation: {sim_name}")
    
    # Simulate a week of trading
    base_time = int(datetime.now().timestamp())
    current_price = 50000.0
    
    print("🔄 Simulating 7 days of trading...")
    
    for day in range(7):
        print(f"  Day {day + 1}:")
        
        # Simulate 24 hours of trading
        for hour in range(24):
            # Simulate price movement
            price_change = (hash(f"{day}{hour}") % 200 - 100) / 10000  # ±1% random movement
            current_price *= (1 + price_change)
            
            # Generate some trades based on conditions
            if hour % 6 == 0:  # Every 6 hours
                # Grid buy
                trade = Trade(
                    id=str(uuid.uuid4()),
                    timestamp=base_time + (day * 24 + hour) * 3600,
                    symbol="BTCUSDT",
                    side="BUY",
                    quantity=0.05,
                    price=current_price,
                    total_value=current_price * 0.05,
                    strategy="GRID",
                    reason="Scheduled grid buy",
                    order_id=f"grid_{day}_{hour}",
                    commission=current_price * 0.05 * 0.001
                )
                sim_manager.execute_trade(trade)
            
            if hour % 8 == 0 and hour > 0:  # Every 8 hours (except first hour)
                # Grid sell
                trade = Trade(
                    id=str(uuid.uuid4()),
                    timestamp=base_time + (day * 24 + hour) * 3600,
                    symbol="BTCUSDT",
                    side="SELL",
                    quantity=0.03,
                    price=current_price,
                    total_value=current_price * 0.03,
                    strategy="GRID",
                    reason="Scheduled grid sell",
                    order_id=f"grid_sell_{day}_{hour}",
                    commission=current_price * 0.03 * 0.001
                )
                sim_manager.execute_trade(trade)
        
        print(f"    💰 End of day {day + 1} balance: ${sim_manager.current_balance:,.2f}")
    
    # Print final summary
    print("\n📊 BACKTEST COMPLETED")
    print("="*50)
    sim_manager.print_summary()
    
    # Export results
    print("\n📄 Exporting results...")
    sim_manager.export_to_csv()
    sim_manager.export_summary_to_json()
    
    print(f"✅ Results exported to simulation_data/{sim_name}_*")
    
    return sim_manager

def main():
    """Main function."""
    print("🎯 BINAGRID SIMULATION EXAMPLES")
    print("="*50)
    
    print("Select simulation type:")
    print("1. Simple Sample Simulation (4 trades)")
    print("2. Backtest Simulation (7 days)")
    print("3. Run both")
    
    choice = input("Enter choice (1-3): ").strip()
    
    if choice == '1':
        run_sample_simulation()
    elif choice == '2':
        run_backtest_simulation()
    elif choice == '3':
        print("\n" + "="*50)
        run_sample_simulation()
        print("\n" + "="*50)
        run_backtest_simulation()
    else:
        print("❌ Invalid choice")
        return
    
    print("\n🎉 Simulation examples completed!")
    print("💡 Use analysis_tool.py to analyze the results:")
    print("   python3 analysis_tool.py --simulation demo_simulation --action summary")
    print("   python3 analysis_tool.py --simulation backtest_simulation --action plot")

if __name__ == "__main__":
    main() 