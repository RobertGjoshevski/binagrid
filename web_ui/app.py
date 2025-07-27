#!/usr/bin/env python3
"""
Web UI for Binagrid Trading Bot
Provides real-time monitoring, analytics, and control interface.
"""

import os
import sys
import json
import sqlite3
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify, request, redirect, url_for
from flask_socketio import SocketIO, emit
import threading
import time

# Add common to path
sys.path.append('../common')
from simulation import SimulationManager

app = Flask(__name__)
app.config['SECRET_KEY'] = 'binagrid-secret-key-2024'
socketio = SocketIO(app, cors_allowed_origins="*")

# Global variables
active_simulations = {}
simulation_data = {}
binance_client = None
live_prices = {}
account_balance = {}

def init_binance_client():
    """Initialize Binance client for live data."""
    global binance_client
    try:
        from binance.client import Client
        from binance.exceptions import BinanceAPIException
        
        # Load API keys from environment
        api_key = os.getenv('BINANCE_API_KEY')
        api_secret = os.getenv('BINANCE_SECRET_KEY')
        testnet = os.getenv('BINANCE_TESTNET', 'True').lower() == 'true'
        
        if api_key and api_secret:
            binance_client = Client(api_key, api_secret, testnet=testnet)
            print("✅ Binance client initialized successfully")
            return True
        else:
            print("⚠️  Binance API keys not found - using demo mode")
            return False
            
    except ImportError:
        print("⚠️  python-binance not installed - using demo mode")
        return False
    except Exception as e:
        print(f"⚠️  Failed to initialize Binance client: {e}")
        return False

def get_live_prices():
    """Get live cryptocurrency prices from Binance."""
    global live_prices
    
    try:
        if binance_client:
            # Get prices for popular cryptocurrencies
            symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'DOTUSDT', 'LINKUSDT']
            
            for symbol in symbols:
                try:
                    ticker = binance_client.get_symbol_ticker(symbol=symbol)
                    live_prices[symbol] = {
                        'price': float(ticker['price']),
                        'timestamp': datetime.now().isoformat()
                    }
                except Exception as e:
                    print(f"Error getting price for {symbol}: {e}")
                    
        else:
            # Demo mode - generate fake prices
            import random
            base_prices = {
                'BTCUSDT': 50000,
                'ETHUSDT': 3000,
                'BNBUSDT': 400,
                'ADAUSDT': 0.5,
                'DOTUSDT': 20,
                'LINKUSDT': 15
            }
            
            for symbol, base_price in base_prices.items():
                # Add some random variation
                variation = random.uniform(-0.02, 0.02)  # ±2%
                live_prices[symbol] = {
                    'price': base_price * (1 + variation),
                    'timestamp': datetime.now().isoformat()
                }
                
    except Exception as e:
        print(f"Error getting live prices: {e}")

def get_account_balance():
    """Get current Binance account balance."""
    global account_balance
    
    try:
        if binance_client:
            account = binance_client.get_account()
            balance_data = {}
            
            for asset in account['balances']:
                free = float(asset['free'])
                locked = float(asset['locked'])
                total = free + locked
                
                if total > 0:  # Only show assets with balance
                    balance_data[asset['asset']] = {
                        'free': free,
                        'locked': locked,
                        'total': total
                    }
            
            account_balance = balance_data
            
        else:
            # Demo mode - show fake balance
            account_balance = {
                'USDT': {'free': 10000.0, 'locked': 0.0, 'total': 10000.0},
                'BTC': {'free': 0.1, 'locked': 0.0, 'total': 0.1},
                'ETH': {'free': 2.5, 'locked': 0.0, 'total': 2.5},
                'BNB': {'free': 10.0, 'locked': 0.0, 'total': 10.0}
            }
            
    except Exception as e:
        print(f"Error getting account balance: {e}")
        # Fallback to demo data
        account_balance = {
            'USDT': {'free': 10000.0, 'locked': 0.0, 'total': 10000.0},
            'BTC': {'free': 0.1, 'locked': 0.0, 'total': 0.1},
            'ETH': {'free': 2.5, 'locked': 0.0, 'total': 2.5},
            'BNB': {'free': 10.0, 'locked': 0.0, 'total': 10.0}
        }

def start_live_data_updates():
    """Start background thread for live data updates."""
    def update_loop():
        while True:
            try:
                get_live_prices()
                get_account_balance()
                
                # Emit live data to connected clients
                socketio.emit('live_data_update', {
                    'prices': live_prices,
                    'balance': account_balance,
                    'timestamp': datetime.now().isoformat()
                }, namespace='/')
                
                time.sleep(5)  # Update every 5 seconds
                
            except Exception as e:
                print(f"Error in live data update loop: {e}")
                time.sleep(10)
    
    update_thread = threading.Thread(target=update_loop)
    update_thread.daemon = True
    update_thread.start()
    print("✅ Live data updates started")

class WebSimulationManager:
    """Web-specific simulation manager with real-time updates."""
    
    def __init__(self, simulation_name: str):
        self.simulation_name = simulation_name
        # Fix path for simulation manager
        os.chdir('../')  # Go to project root
        self.sim_manager = SimulationManager(simulation_name)
        os.chdir('web_ui')  # Go back to web_ui directory
        self.is_running = False
        self.update_thread = None
        
    def start_monitoring(self):
        """Start real-time monitoring."""
        if not self.is_running:
            self.is_running = True
            self.update_thread = threading.Thread(target=self._monitor_loop)
            self.update_thread.daemon = True
            self.update_thread.start()
    
    def stop_monitoring(self):
        """Stop real-time monitoring."""
        self.is_running = False
        if self.update_thread:
            self.update_thread.join()
    
    def _monitor_loop(self):
        """Monitor loop for real-time updates."""
        while self.is_running:
            try:
                # Get current data
                data = self.get_current_data()
                
                # Emit to connected clients
                socketio.emit('simulation_update', {
                    'simulation_name': self.simulation_name,
                    'data': data
                }, namespace='/')
                
                time.sleep(5)  # Update every 5 seconds
                
            except Exception as e:
                print(f"Monitoring error: {e}")
                time.sleep(10)
    
    def get_current_data(self):
        """Get current simulation data."""
        analysis = self.sim_manager.get_analysis_data()
        
        # Get recent trades
        trades_df = self._load_recent_trades()
        recent_trades = []
        
        if not trades_df.empty:
            recent_trades = trades_df.tail(10).to_dict('records')
        
        return {
            'analysis': analysis,
            'recent_trades': recent_trades,
            'current_balance': self.sim_manager.current_balance,
            'total_return_percent': analysis['total_return_percent'],
            'total_trades': analysis['total_trades'],
            'win_rate': analysis['performance_metrics']['win_rate'] * 100,
            'total_pnl': analysis['performance_metrics']['total_pnl']
        }
    
    def _load_recent_trades(self):
        """Load recent trades from database."""
        try:
            conn = sqlite3.connect(self.sim_manager.db_path)
            query = "SELECT * FROM trades ORDER BY timestamp DESC LIMIT 10"
            df = pd.read_sql_query(query, conn)
            conn.close()
            
            if not df.empty:
                df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')
            
            return df
        except Exception as e:
            print(f"Error loading trades: {e}")
            return pd.DataFrame()

def get_available_simulations():
    """Get list of available simulations."""
    simulations = []
    sim_dir = "../simulation_data"  # Fix path to simulation data
    
    if os.path.exists(sim_dir):
        for file in os.listdir(sim_dir):
            if file.endswith('.db'):
                sim_name = file.replace('.db', '')
                simulations.append(sim_name)
    
    return simulations

@app.route('/')
def index():
    """Main dashboard page."""
    simulations = get_available_simulations()
    return render_template('index.html', simulations=simulations)

@app.route('/dashboard/<simulation_name>')
def dashboard(simulation_name):
    """Simulation dashboard page."""
    return render_template('dashboard.html', simulation_name=simulation_name)

@app.route('/api/live-data')
def get_live_data():
    """Get live market data API endpoint."""
    return jsonify({
        'success': True,
        'prices': live_prices,
        'balance': account_balance,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/simulation/<simulation_name>/data')
def get_simulation_data(simulation_name):
    """Get simulation data API endpoint."""
    try:
        # Fix path for simulation manager
        original_dir = os.getcwd()
        os.chdir('../')  # Go to project root
        
        sim_manager = SimulationManager(simulation_name)
        data = sim_manager.get_analysis_data()
        
        # Get trade history for charts
        trades_df = sim_manager.load_trades_data()
        
        os.chdir(original_dir)  # Go back to original directory
        
        if not trades_df.empty:
            # Prepare chart data
            trades_df['cumulative_pnl'] = trades_df['realized_pnl'].cumsum()
            trades_df['datetime'] = pd.to_datetime(trades_df['timestamp'], unit='s')
            
            chart_data = {
                'timestamps': trades_df['datetime'].dt.strftime('%Y-%m-%d %H:%M:%S').tolist(),
                'cumulative_pnl': trades_df['cumulative_pnl'].tolist(),
                'prices': trades_df['price'].tolist(),
                'volumes': trades_df['total_value'].tolist()
            }
        else:
            chart_data = {
                'timestamps': [],
                'cumulative_pnl': [],
                'prices': [],
                'volumes': []
            }
        
        return jsonify({
            'success': True,
            'data': data,
            'chart_data': chart_data
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/simulation/<simulation_name>/trades')
def get_simulation_trades(simulation_name):
    """Get simulation trades API endpoint."""
    try:
        # Fix path for simulation manager
        original_dir = os.getcwd()
        os.chdir('../')  # Go to project root
        
        sim_manager = SimulationManager(simulation_name)
        trades_df = sim_manager.load_trades_data()
        
        os.chdir(original_dir)  # Go back to original directory
        
        if not trades_df.empty:
            trades = trades_df.tail(50).to_dict('records')  # Last 50 trades
            for trade in trades:
                trade['datetime'] = pd.to_datetime(trade['timestamp'], unit='s').strftime('%Y-%m-%d %H:%M:%S')
        else:
            trades = []
        
        return jsonify({
            'success': True,
            'trades': trades
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/simulation/<simulation_name>/performance')
def get_simulation_performance(simulation_name):
    """Get detailed performance metrics."""
    try:
        # Fix path for simulation manager
        original_dir = os.getcwd()
        os.chdir('../')  # Go to project root
        
        sim_manager = SimulationManager(simulation_name)
        trades_df = sim_manager.load_trades_data()
        
        os.chdir(original_dir)  # Go back to original directory
        
        if trades_df.empty:
            return jsonify({
                'success': False,
                'error': 'No data available'
            })
        
        # Calculate detailed metrics
        trades_df['hour'] = trades_df['datetime'].dt.hour
        trades_df['day_of_week'] = trades_df['datetime'].dt.day_name()
        
        hourly_performance = trades_df.groupby('hour')['realized_pnl'].sum().to_dict()
        daily_performance = trades_df.groupby('day_of_week')['realized_pnl'].sum().to_dict()
        
        # Strategy breakdown
        strategy_performance = trades_df.groupby('strategy').agg({
            'realized_pnl': ['sum', 'count', 'mean'],
            'total_value': 'sum'
        }).round(2).to_dict()
        
        return jsonify({
            'success': True,
            'hourly_performance': hourly_performance,
            'daily_performance': daily_performance,
            'strategy_performance': strategy_performance
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/simulations')
def get_simulations_list():
    """Get list of all simulations."""
    simulations = get_available_simulations()
    
    # Get basic info for each simulation
    sim_info = []
    for sim_name in simulations:
        try:
            # Fix path for simulation manager
            original_dir = os.getcwd()
            os.chdir('../')  # Go to project root
            
            sim_manager = SimulationManager(sim_name)
            analysis = sim_manager.get_analysis_data()
            
            os.chdir(original_dir)  # Go back to original directory
            
            sim_info.append({
                'name': sim_name,
                'total_trades': analysis['total_trades'],
                'total_return': analysis['total_return_percent'],
                'total_pnl': analysis['performance_metrics']['total_pnl'],
                'win_rate': analysis['performance_metrics']['win_rate'] * 100,
                'duration_days': analysis['simulation_duration_days']
            })
        except Exception as e:
            sim_info.append({
                'name': sim_name,
                'error': str(e)
            })
    
    return jsonify({
        'success': True,
        'simulations': sim_info
    })

@app.route('/api/simulation/<simulation_name>/start')
def start_simulation(simulation_name):
    """Start a simulation."""
    try:
        if simulation_name not in active_simulations:
            active_simulations[simulation_name] = WebSimulationManager(simulation_name)
        
        active_simulations[simulation_name].start_monitoring()
        
        return jsonify({
            'success': True,
            'message': f'Simulation {simulation_name} started'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/simulation/<simulation_name>/stop')
def stop_simulation(simulation_name):
    """Stop a simulation."""
    try:
        if simulation_name in active_simulations:
            active_simulations[simulation_name].stop_monitoring()
            del active_simulations[simulation_name]
        
        return jsonify({
            'success': True,
            'message': f'Simulation {simulation_name} stopped'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    print('Client connected')
    emit('status', {'message': 'Connected to Binagrid Web UI'})
    
    # Send initial live data
    emit('live_data_update', {
        'prices': live_prices,
        'balance': account_balance,
        'timestamp': datetime.now().isoformat()
    })

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection."""
    print('Client disconnected')

@socketio.on('join_simulation')
def handle_join_simulation(data):
    """Handle joining a simulation room."""
    simulation_name = data.get('simulation_name')
    if simulation_name:
        # Join room for this simulation
        join_room(simulation_name)
        emit('status', {'message': f'Joined simulation: {simulation_name}'})

if __name__ == '__main__':
    print("🌐 Starting Binagrid Web UI...")
    print("📊 Dashboard will be available at: http://localhost:8080")
    
    # Import pandas here to avoid circular imports
    import pandas as pd
    
    # Initialize Binance client and start live data updates
    init_binance_client()
    start_live_data_updates()
    
    socketio.run(app, host='0.0.0.0', port=8080, debug=True) 