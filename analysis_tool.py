#!/usr/bin/env python3
"""
Analysis Tool for Trading Bot Simulations
Provides comprehensive analysis and visualization of simulation results.
"""

import sys
import os
import argparse
import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
from typing import Dict, List, Any, Optional
import sqlite3

# Add common to path
sys.path.append('common')
from simulation import SimulationManager

class SimulationAnalyzer:
    """Analyzes simulation results and generates reports."""
    
    def __init__(self, simulation_name: str = "default"):
        self.simulation_name = simulation_name
        self.sim_manager = SimulationManager(simulation_name)
        self.db_path = f"simulation_data/{simulation_name}.db"
        
    def load_trades_data(self) -> pd.DataFrame:
        """Load trades data from database."""
        if not os.path.exists(self.db_path):
            print(f"❌ Simulation database not found: {self.db_path}")
            return pd.DataFrame()
        
        conn = sqlite3.connect(self.db_path)
        query = "SELECT * FROM trades ORDER BY timestamp"
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        # Convert timestamp to datetime
        df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')
        df['date'] = df['datetime'].dt.date
        
        return df
    
    def load_performance_data(self) -> pd.DataFrame:
        """Load performance data from database."""
        if not os.path.exists(self.db_path):
            return pd.DataFrame()
        
        conn = sqlite3.connect(self.db_path)
        query = "SELECT * FROM performance ORDER BY timestamp"
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        # Convert timestamp to datetime
        df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')
        
        return df
    
    def generate_summary_report(self) -> Dict[str, Any]:
        """Generate comprehensive summary report."""
        trades_df = self.load_trades_data()
        
        if trades_df.empty:
            return {"error": "No simulation data found"}
        
        # Basic statistics
        total_trades = len(trades_df)
        total_volume = trades_df['total_value'].sum()
        total_commission = trades_df['commission'].sum()
        
        # PnL analysis
        realized_trades = trades_df[trades_df['realized_pnl'] != 0]
        winning_trades = realized_trades[realized_trades['realized_pnl'] > 0]
        losing_trades = realized_trades[realized_trades['realized_pnl'] < 0]
        
        total_pnl = realized_trades['realized_pnl'].sum()
        win_rate = len(winning_trades) / len(realized_trades) if len(realized_trades) > 0 else 0
        
        # Strategy analysis
        strategy_stats = trades_df.groupby('strategy').agg({
            'realized_pnl': ['sum', 'count', 'mean'],
            'total_value': 'sum'
        }).round(2)
        
        # Time analysis
        trades_df['hour'] = trades_df['datetime'].dt.hour
        trades_df['day_of_week'] = trades_df['datetime'].dt.day_name()
        
        hourly_stats = trades_df.groupby('hour')['realized_pnl'].sum()
        daily_stats = trades_df.groupby('day_of_week')['realized_pnl'].sum()
        
        # Calculate drawdown
        cumulative_pnl = trades_df['realized_pnl'].cumsum()
        running_max = cumulative_pnl.expanding().max()
        drawdown = (cumulative_pnl - running_max) / running_max * 100
        max_drawdown = drawdown.min()
        
        return {
            'simulation_name': self.simulation_name,
            'total_trades': total_trades,
            'total_volume': total_volume,
            'total_commission': total_commission,
            'total_pnl': total_pnl,
            'win_rate': win_rate,
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'max_drawdown': max_drawdown,
            'strategy_stats': strategy_stats.to_dict(),
            'hourly_stats': hourly_stats.to_dict(),
            'daily_stats': daily_stats.to_dict(),
            'start_date': trades_df['datetime'].min(),
            'end_date': trades_df['datetime'].max(),
            'duration_days': (trades_df['datetime'].max() - trades_df['datetime'].min()).days
        }
    
    def plot_pnl_over_time(self, save_path: str = None):
        """Plot PnL over time."""
        trades_df = self.load_trades_data()
        
        if trades_df.empty:
            print("❌ No data to plot")
            return
        
        plt.figure(figsize=(12, 6))
        
        # Calculate cumulative PnL
        trades_df['cumulative_pnl'] = trades_df['realized_pnl'].cumsum()
        
        plt.plot(trades_df['datetime'], trades_df['cumulative_pnl'], linewidth=2)
        plt.title(f'Cumulative PnL Over Time - {self.simulation_name}')
        plt.xlabel('Date')
        plt.ylabel('Cumulative PnL (USDT)')
        plt.grid(True, alpha=0.3)
        
        # Add zero line
        plt.axhline(y=0, color='red', linestyle='--', alpha=0.5)
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"📊 Chart saved to: {save_path}")
        else:
            plt.show()
        
        plt.close()
    
    def plot_trade_distribution(self, save_path: str = None):
        """Plot trade distribution by strategy and side."""
        trades_df = self.load_trades_data()
        
        if trades_df.empty:
            print("❌ No data to plot")
            return
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # Strategy distribution
        strategy_counts = trades_df['strategy'].value_counts()
        ax1.pie(strategy_counts.values, labels=strategy_counts.index, autopct='%1.1f%%')
        ax1.set_title('Trade Distribution by Strategy')
        
        # Side distribution
        side_counts = trades_df['side'].value_counts()
        ax2.pie(side_counts.values, labels=side_counts.index, autopct='%1.1f%%')
        ax2.set_title('Trade Distribution by Side')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"📊 Chart saved to: {save_path}")
        else:
            plt.show()
        
        plt.close()
    
    def plot_hourly_performance(self, save_path: str = None):
        """Plot performance by hour of day."""
        trades_df = self.load_trades_data()
        
        if trades_df.empty:
            print("❌ No data to plot")
            return
        
        hourly_pnl = trades_df.groupby('hour')['realized_pnl'].sum()
        
        plt.figure(figsize=(10, 6))
        bars = plt.bar(hourly_pnl.index, hourly_pnl.values)
        
        # Color bars based on positive/negative
        for bar, value in zip(bars, hourly_pnl.values):
            if value >= 0:
                bar.set_color('green')
            else:
                bar.set_color('red')
        
        plt.title(f'Hourly Performance - {self.simulation_name}')
        plt.xlabel('Hour of Day')
        plt.ylabel('Total PnL (USDT)')
        plt.grid(True, alpha=0.3)
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"📊 Chart saved to: {save_path}")
        else:
            plt.show()
        
        plt.close()
    
    def generate_csv_report(self, output_path: str = None):
        """Generate detailed CSV report."""
        trades_df = self.load_trades_data()
        
        if trades_df.empty:
            print("❌ No data to export")
            return
        
        if not output_path:
            output_path = f"simulation_data/{self.simulation_name}_analysis.csv"
        
        # Add additional analysis columns
        trades_df['cumulative_pnl'] = trades_df['realized_pnl'].cumsum()
        trades_df['trade_number'] = range(1, len(trades_df) + 1)
        
        # Export to CSV
        trades_df.to_csv(output_path, index=False)
        print(f"📄 Detailed report exported to: {output_path}")
    
    def print_detailed_analysis(self):
        """Print detailed analysis to console."""
        report = self.generate_summary_report()
        
        if 'error' in report:
            print(f"❌ {report['error']}")
            return
        
        print("\n" + "="*80)
        print(f"📊 DETAILED ANALYSIS: {self.simulation_name}")
        print("="*80)
        
        print(f"📅 Period: {report['start_date']} to {report['end_date']}")
        print(f"⏱️  Duration: {report['duration_days']} days")
        print()
        
        print("💰 PERFORMANCE METRICS:")
        print(f"   Total Trades: {report['total_trades']}")
        print(f"   Total Volume: ${report['total_volume']:,.2f}")
        print(f"   Total PnL: ${report['total_pnl']:,.2f}")
        print(f"   Total Commission: ${report['total_commission']:,.2f}")
        print(f"   Win Rate: {report['win_rate']*100:.2f}%")
        print(f"   Winning Trades: {report['winning_trades']}")
        print(f"   Losing Trades: {report['losing_trades']}")
        print(f"   Max Drawdown: {report['max_drawdown']:.2f}%")
        print()
        
        print("📈 STRATEGY BREAKDOWN:")
        for strategy, stats in report['strategy_stats'].items():
            print(f"   {strategy}:")
            print(f"     Trades: {stats['realized_pnl']['count']}")
            print(f"     Total PnL: ${stats['realized_pnl']['sum']:,.2f}")
            print(f"     Avg PnL: ${stats['realized_pnl']['mean']:,.2f}")
            print(f"     Volume: ${stats['total_value']['sum']:,.2f}")
        print()
        
        print("🕐 BEST PERFORMING HOURS:")
        hourly_sorted = sorted(report['hourly_stats'].items(), key=lambda x: x[1], reverse=True)
        for hour, pnl in hourly_sorted[:5]:
            print(f"   {hour:02d}:00 - ${pnl:,.2f}")
        print()
        
        print("📅 BEST PERFORMING DAYS:")
        daily_sorted = sorted(report['daily_stats'].items(), key=lambda x: x[1], reverse=True)
        for day, pnl in daily_sorted:
            print(f"   {day} - ${pnl:,.2f}")
        
        print("="*80)
    
    def compare_simulations(self, other_simulation: str):
        """Compare two simulations."""
        report1 = self.generate_summary_report()
        report2 = SimulationAnalyzer(other_simulation).generate_summary_report()
        
        if 'error' in report1 or 'error' in report2:
            print("❌ Cannot compare simulations - missing data")
            return
        
        print("\n" + "="*80)
        print(f"📊 SIMULATION COMPARISON: {self.simulation_name} vs {other_simulation}")
        print("="*80)
        
        metrics = ['total_trades', 'total_pnl', 'win_rate', 'max_drawdown']
        
        for metric in metrics:
            val1 = report1[metric]
            val2 = report2[metric]
            
            if isinstance(val1, float):
                print(f"{metric.replace('_', ' ').title()}:")
                print(f"   {self.simulation_name}: {val1:.2f}")
                print(f"   {other_simulation}: {val2:.2f}")
                print(f"   Difference: {val1 - val2:.2f}")
            else:
                print(f"{metric.replace('_', ' ').title()}:")
                print(f"   {self.simulation_name}: {val1}")
                print(f"   {other_simulation}: {val2}")
                print(f"   Difference: {val1 - val2}")
            print()
        
        print("="*80)

def main():
    """Main entry point for analysis tool."""
    parser = argparse.ArgumentParser(description='Trading Bot Simulation Analyzer')
    parser.add_argument('--simulation', '-s', default='default',
                       help='Simulation name to analyze')
    parser.add_argument('--action', '-a', 
                       choices=['summary', 'plot', 'export', 'compare'],
                       default='summary',
                       help='Analysis action to perform')
    parser.add_argument('--compare-with', '-c',
                       help='Simulation to compare with (for compare action)')
    parser.add_argument('--output', '-o',
                       help='Output file path for plots/exports')
    
    args = parser.parse_args()
    
    analyzer = SimulationAnalyzer(args.simulation)
    
    if args.action == 'summary':
        analyzer.print_detailed_analysis()
    
    elif args.action == 'plot':
        if not args.output:
            args.output = f"simulation_data/{args.simulation}_analysis.png"
        
        analyzer.plot_pnl_over_time(args.output.replace('.png', '_pnl.png'))
        analyzer.plot_trade_distribution(args.output.replace('.png', '_distribution.png'))
        analyzer.plot_hourly_performance(args.output.replace('.png', '_hourly.png'))
    
    elif args.action == 'export':
        analyzer.generate_csv_report(args.output)
    
    elif args.action == 'compare':
        if not args.compare_with:
            print("❌ Please specify a simulation to compare with using --compare-with")
            return
        analyzer.compare_simulations(args.compare_with)

if __name__ == "__main__":
    main() 