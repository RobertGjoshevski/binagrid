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

class WebSimulationManager:
    """Web-specific simulation manager with real-time updates."""
    
    def __init__(self, simulation_name: str):
        self.simulation_name = simulation_name
        self.sim_manager = SimulationManager(simulation_name)
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
    sim_dir = "simulation_data"
    
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

@app.route('/api/simulation/<simulation_name>/data')
def get_simulation_data(simulation_name):
    """Get simulation data API endpoint."""
    try:
        sim_manager = SimulationManager(simulation_name)
        data = sim_manager.get_analysis_data()
        
        # Get trade history for charts
        trades_df = sim_manager.load_trades_data()
        
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
        sim_manager = SimulationManager(simulation_name)
        trades_df = sim_manager.load_trades_data()
        
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
        sim_manager = SimulationManager(simulation_name)
        trades_df = sim_manager.load_trades_data()
        
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
            sim_manager = SimulationManager(sim_name)
            analysis = sim_manager.get_analysis_data()
            
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
    print("📊 Dashboard will be available at: http://localhost:5000")
    
    # Import pandas here to avoid circular imports
    import pandas as pd
    
    socketio.run(app, host='0.0.0.0', port=5000, debug=True) 