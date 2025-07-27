"""
Simulation module for paper trading with comprehensive data storage and analysis.
"""

import json
import csv
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import os
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)

@dataclass
class Trade:
    """Trade data structure for simulation."""
    id: str
    timestamp: int
    symbol: str
    side: str  # BUY, SELL
    quantity: float
    price: float
    total_value: float
    strategy: str
    reason: str
    order_id: str
    commission: float = 0.0
    realized_pnl: float = 0.0
    unrealized_pnl: float = 0.0

@dataclass
class Position:
    """Position data structure for simulation."""
    symbol: str
    quantity: float
    avg_price: float
    total_cost: float
    current_value: float
    unrealized_pnl: float
    realized_pnl: float
    last_updated: int

@dataclass
class PerformanceMetrics:
    """Performance metrics data structure."""
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_pnl: float
    total_volume: float
    avg_trade_size: float
    max_drawdown: float
    sharpe_ratio: float
    profit_factor: float
    total_commission: float

class SimulationManager:
    """Manages paper trading simulation with comprehensive data storage."""
    
    def __init__(self, simulation_name: str = "default"):
        self.simulation_name = simulation_name
        self.db_path = f"simulation_data/{simulation_name}.db"
        self.csv_path = f"simulation_data/{simulation_name}_trades.csv"
        self.json_path = f"simulation_data/{simulation_name}_summary.json"
        
        # Create simulation data directory
        os.makedirs("simulation_data", exist_ok=True)
        
        # Initialize database
        self._init_database()
        
        # Current positions
        self.positions: Dict[str, Position] = {}
        
        # Performance tracking
        self.initial_balance = 10000.0  # Starting with 10,000 USDT
        self.current_balance = self.initial_balance
        self.trade_history: List[Trade] = []
        
        logger.info(f"Simulation '{simulation_name}' initialized with ${self.initial_balance} starting balance")
    
    def _init_database(self):
        """Initialize SQLite database for simulation data."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create trades table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trades (
                id TEXT PRIMARY KEY,
                timestamp INTEGER,
                symbol TEXT,
                side TEXT,
                quantity REAL,
                price REAL,
                total_value REAL,
                strategy TEXT,
                reason TEXT,
                order_id TEXT,
                commission REAL,
                realized_pnl REAL,
                unrealized_pnl REAL
            )
        ''')
        
        # Create positions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS positions (
                symbol TEXT PRIMARY KEY,
                quantity REAL,
                avg_price REAL,
                total_cost REAL,
                current_value REAL,
                unrealized_pnl REAL,
                realized_pnl REAL,
                last_updated INTEGER
            )
        ''')
        
        # Create performance table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS performance (
                timestamp INTEGER PRIMARY KEY,
                total_trades INTEGER,
                winning_trades INTEGER,
                losing_trades INTEGER,
                win_rate REAL,
                total_pnl REAL,
                total_volume REAL,
                avg_trade_size REAL,
                max_drawdown REAL,
                sharpe_ratio REAL,
                profit_factor REAL,
                total_commission REAL,
                current_balance REAL
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def execute_trade(self, trade: Trade) -> bool:
        """Execute a simulated trade and update positions."""
        try:
            # Update balance
            if trade.side == "BUY":
                self.current_balance -= trade.total_value
            else:  # SELL
                self.current_balance += trade.total_value
            
            # Update positions
            self._update_position(trade)
            
            # Store trade
            self._store_trade(trade)
            self.trade_history.append(trade)
            
            # Update performance metrics
            self._update_performance_metrics()
            
            logger.info(f"Simulated {trade.side} trade: {trade.quantity} {trade.symbol} @ ${trade.price:.2f}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to execute simulated trade: {e}")
            return False
    
    def _update_position(self, trade: Trade):
        """Update position based on trade."""
        symbol = trade.symbol
        
        if symbol not in self.positions:
            self.positions[symbol] = Position(
                symbol=symbol,
                quantity=0.0,
                avg_price=0.0,
                total_cost=0.0,
                current_value=0.0,
                unrealized_pnl=0.0,
                realized_pnl=0.0,
                last_updated=trade.timestamp
            )
        
        position = self.positions[symbol]
        
        if trade.side == "BUY":
            # Calculate new average price
            total_quantity = position.quantity + trade.quantity
            total_cost = position.total_cost + trade.total_value
            
            if total_quantity > 0:
                position.avg_price = total_cost / total_quantity
            
            position.quantity = total_quantity
            position.total_cost = total_cost
            
        else:  # SELL
            if position.quantity >= trade.quantity:
                # Calculate realized PnL
                realized_pnl = (trade.price - position.avg_price) * trade.quantity
                position.realized_pnl += realized_pnl
                
                # Update position
                position.quantity -= trade.quantity
                position.total_cost = position.avg_price * position.quantity
                
                # Update trade with realized PnL
                trade.realized_pnl = realized_pnl
                
                # Remove position if quantity is 0
                if position.quantity <= 0:
                    del self.positions[symbol]
        
        position.last_updated = trade.timestamp
    
    def _store_trade(self, trade: Trade):
        """Store trade in database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO trades 
            (id, timestamp, symbol, side, quantity, price, total_value, strategy, reason, order_id, commission, realized_pnl, unrealized_pnl)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            trade.id, trade.timestamp, trade.symbol, trade.side, trade.quantity,
            trade.price, trade.total_value, trade.strategy, trade.reason,
            trade.order_id, trade.commission, trade.realized_pnl, trade.unrealized_pnl
        ))
        
        conn.commit()
        conn.close()
    
    def _update_performance_metrics(self):
        """Update and store performance metrics."""
        metrics = self.calculate_performance_metrics()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO performance 
            (timestamp, total_trades, winning_trades, losing_trades, win_rate, total_pnl, 
             total_volume, avg_trade_size, max_drawdown, sharpe_ratio, profit_factor, 
             total_commission, current_balance)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            int(datetime.now().timestamp()), metrics.total_trades, metrics.winning_trades,
            metrics.losing_trades, metrics.win_rate, metrics.total_pnl, metrics.total_volume,
            metrics.avg_trade_size, metrics.max_drawdown, metrics.sharpe_ratio,
            metrics.profit_factor, metrics.total_commission, self.current_balance
        ))
        
        conn.commit()
        conn.close()
    
    def calculate_performance_metrics(self) -> PerformanceMetrics:
        """Calculate comprehensive performance metrics."""
        if not self.trade_history:
            return PerformanceMetrics(
                total_trades=0, winning_trades=0, losing_trades=0, win_rate=0.0,
                total_pnl=0.0, total_volume=0.0, avg_trade_size=0.0, max_drawdown=0.0,
                sharpe_ratio=0.0, profit_factor=0.0, total_commission=0.0
            )
        
        # Basic metrics
        total_trades = len(self.trade_history)
        total_volume = sum(trade.total_value for trade in self.trade_history)
        total_commission = sum(trade.commission for trade in self.trade_history)
        
        # PnL analysis
        realized_trades = [trade for trade in self.trade_history if trade.realized_pnl != 0]
        winning_trades = [trade for trade in realized_trades if trade.realized_pnl > 0]
        losing_trades = [trade for trade in realized_trades if trade.realized_pnl < 0]
        
        total_pnl = sum(trade.realized_pnl for trade in realized_trades)
        win_rate = len(winning_trades) / len(realized_trades) if realized_trades else 0.0
        
        # Calculate profit factor
        gross_profit = sum(trade.realized_pnl for trade in winning_trades)
        gross_loss = abs(sum(trade.realized_pnl for trade in losing_trades))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        # Calculate max drawdown
        max_drawdown = self._calculate_max_drawdown()
        
        # Calculate Sharpe ratio (simplified)
        sharpe_ratio = self._calculate_sharpe_ratio()
        
        return PerformanceMetrics(
            total_trades=total_trades,
            winning_trades=len(winning_trades),
            losing_trades=len(losing_trades),
            win_rate=win_rate,
            total_pnl=total_pnl,
            total_volume=total_volume,
            avg_trade_size=total_volume / total_trades if total_trades > 0 else 0.0,
            max_drawdown=max_drawdown,
            sharpe_ratio=sharpe_ratio,
            profit_factor=profit_factor,
            total_commission=total_commission
        )
    
    def _calculate_max_drawdown(self) -> float:
        """Calculate maximum drawdown."""
        if not self.trade_history:
            return 0.0
        
        # Calculate running balance
        balance = self.initial_balance
        peak_balance = balance
        max_drawdown = 0.0
        
        for trade in self.trade_history:
            if trade.realized_pnl != 0:
                balance += trade.realized_pnl
                peak_balance = max(peak_balance, balance)
                drawdown = (peak_balance - balance) / peak_balance
                max_drawdown = max(max_drawdown, drawdown)
        
        return max_drawdown * 100  # Return as percentage
    
    def _calculate_sharpe_ratio(self) -> float:
        """Calculate Sharpe ratio (simplified)."""
        if not self.trade_history:
            return 0.0
        
        # Get daily returns
        daily_returns = self._get_daily_returns()
        
        if not daily_returns:
            return 0.0
        
        avg_return = sum(daily_returns) / len(daily_returns)
        std_return = (sum((r - avg_return) ** 2 for r in daily_returns) / len(daily_returns)) ** 0.5
        
        if std_return == 0:
            return 0.0
        
        # Assuming risk-free rate of 0 for simplicity
        return avg_return / std_return
    
    def _get_daily_returns(self) -> List[float]:
        """Get daily returns for Sharpe ratio calculation."""
        # Group trades by day and calculate daily PnL
        daily_pnl = {}
        
        for trade in self.trade_history:
            if trade.realized_pnl != 0:
                date = datetime.fromtimestamp(trade.timestamp).date()
                daily_pnl[date] = daily_pnl.get(date, 0.0) + trade.realized_pnl
        
        # Convert to returns
        returns = []
        for date, pnl in sorted(daily_pnl.items()):
            returns.append(pnl / self.initial_balance)
        
        return returns
    
    def export_to_csv(self):
        """Export trade history to CSV file."""
        if not self.trade_history:
            logger.warning("No trades to export")
            return
        
        with open(self.csv_path, 'w', newline='') as csvfile:
            fieldnames = ['id', 'timestamp', 'datetime', 'symbol', 'side', 'quantity', 
                         'price', 'total_value', 'strategy', 'reason', 'order_id', 
                         'commission', 'realized_pnl', 'unrealized_pnl']
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for trade in self.trade_history:
                row = asdict(trade)
                row['datetime'] = datetime.fromtimestamp(trade.timestamp).strftime('%Y-%m-%d %H:%M:%S')
                writer.writerow(row)
        
        logger.info(f"Trade history exported to {self.csv_path}")
    
    def export_summary_to_json(self):
        """Export performance summary to JSON file."""
        metrics = self.calculate_performance_metrics()
        
        summary = {
            'simulation_name': self.simulation_name,
            'start_date': datetime.fromtimestamp(self.trade_history[0].timestamp).isoformat() if self.trade_history else None,
            'end_date': datetime.fromtimestamp(self.trade_history[-1].timestamp).isoformat() if self.trade_history else None,
            'initial_balance': self.initial_balance,
            'current_balance': self.current_balance,
            'total_return': ((self.current_balance - self.initial_balance) / self.initial_balance) * 100,
            'performance_metrics': asdict(metrics),
            'current_positions': {symbol: asdict(pos) for symbol, pos in self.positions.items()}
        }
        
        with open(self.json_path, 'w') as jsonfile:
            json.dump(summary, jsonfile, indent=2)
        
        logger.info(f"Performance summary exported to {self.json_path}")
    
    def get_analysis_data(self) -> Dict[str, Any]:
        """Get comprehensive analysis data."""
        metrics = self.calculate_performance_metrics()
        
        return {
            'simulation_name': self.simulation_name,
            'performance_metrics': asdict(metrics),
            'current_balance': self.current_balance,
            'total_return_percent': ((self.current_balance - self.initial_balance) / self.initial_balance) * 100,
            'current_positions': len(self.positions),
            'total_trades': len(self.trade_history),
            'simulation_duration_days': self._get_simulation_duration_days()
        }
    
    def _get_simulation_duration_days(self) -> int:
        """Get simulation duration in days."""
        if not self.trade_history:
            return 0
        
        start_time = self.trade_history[0].timestamp
        end_time = self.trade_history[-1].timestamp
        
        duration_seconds = end_time - start_time
        return duration_seconds // (24 * 3600)  # Convert to days
    
    def print_summary(self):
        """Print simulation summary."""
        analysis = self.get_analysis_data()
        metrics = analysis['performance_metrics']
        
        print("\n" + "="*60)
        print(f"📊 SIMULATION SUMMARY: {self.simulation_name}")
        print("="*60)
        print(f"💰 Initial Balance: ${self.initial_balance:,.2f}")
        print(f"💰 Current Balance: ${self.current_balance:,.2f}")
        print(f"📈 Total Return: {analysis['total_return_percent']:.2f}%")
        print(f"📊 Total Trades: {metrics['total_trades']}")
        print(f"✅ Winning Trades: {metrics['winning_trades']}")
        print(f"❌ Losing Trades: {metrics['losing_trades']}")
        print(f"🎯 Win Rate: {metrics['win_rate']*100:.2f}%")
        print(f"💵 Total PnL: ${metrics['total_pnl']:,.2f}")
        print(f"📊 Total Volume: ${metrics['total_volume']:,.2f}")
        print(f"📉 Max Drawdown: {metrics['max_drawdown']:.2f}%")
        print(f"📈 Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
        print(f"💰 Profit Factor: {metrics['profit_factor']:.2f}")
        print(f"💸 Total Commission: ${metrics['total_commission']:,.2f}")
        print(f"⏱️  Duration: {analysis['simulation_duration_days']} days")
        print("="*60) 