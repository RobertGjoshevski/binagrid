"""
Grid Trading Bot implementation.
Implements grid trading strategy using Binance API.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'common'))

import time
import logging
import signal
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from binance.client import Client
from binance.exceptions import BinanceAPIException
from binance.enums import *
import pandas as pd

from config import Config, get_trading_pair_config
from utils import (
    calculate_grid_levels,
    format_quantity,
    format_price,
    calculate_order_size,
    validate_order_parameters,
    retry_on_error,
    log_trade_execution,
    calculate_pnl,
    get_current_timestamp
)
from grid_config import GridConfig

# Set up logging
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class GridTradingBot:
    """
    Grid Trading Bot class.
    Implements grid trading strategy with automatic order management.
    """
    
    def __init__(self):
        """Initialize the Grid Trading Bot."""
        self.client = None
        self.symbol = Config.TRADING_PAIR
        self.grid_levels = []
        self.active_orders = {}
        self.executed_orders = []
        self.positions = []
        self.is_running = False
        self.start_time = None
        self.daily_pnl = 0.0
        self.last_rebalance = None
        
        # Initialize Binance client
        self._initialize_client()
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _initialize_client(self):
        """Initialize Binance API client."""
        try:
            binance_config = Config.get_binance_config()
            self.client = Client(
                api_key=binance_config['api_key'],
                api_secret=binance_config['api_secret'],
                testnet=binance_config.get('testnet', False)
            )
            
            # Test connection
            server_time = self.client.get_server_time()
            logger.info(f"Connected to Binance API. Server time: {server_time}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Binance client: {e}")
            raise
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}. Shutting down gracefully...")
        self.stop()
        sys.exit(0)
    
    @retry_on_error
    def get_current_price(self) -> float:
        """Get current market price for the trading pair."""
        ticker = self.client.get_symbol_ticker(symbol=self.symbol)
        return float(ticker['price'])
    
    @retry_on_error
    def get_account_info(self) -> Dict[str, Any]:
        """Get account information and balances."""
        account = self.client.get_account()
        return account
    
    def get_balance(self, asset: str) -> float:
        """Get balance for a specific asset."""
        account = self.get_account_info()
        for balance in account['balances']:
            if balance['asset'] == asset:
                return float(balance['free'])
        return 0.0
    
    def calculate_initial_grid(self) -> List[float]:
        """Calculate initial grid levels based on current price."""
        current_price = self.get_current_price()
        logger.info(f"Current {self.symbol} price: {current_price}")
        
        self.grid_levels = calculate_grid_levels(
            current_price=current_price,
            grid_levels=GridConfig.GRID_LEVELS,
            grid_spacing_percent=GridConfig.GRID_SPACING_PERCENT,
            grid_type=GridConfig.GRID_TYPE
        )
        
        logger.info(f"Generated {len(self.grid_levels)} grid levels: {self.grid_levels}")
        return self.grid_levels
    
    @retry_on_error
    def place_grid_orders(self) -> Dict[str, Any]:
        """Place initial grid orders."""
        if not self.grid_levels:
            self.calculate_initial_grid()
        
        current_price = self.get_current_price()
        placed_orders = {}
        
        for i, level_price in enumerate(self.grid_levels):
            # Determine order side based on price level
            if level_price < current_price:
                side = SIDE_BUY
                order_size = calculate_order_size(
                    GridConfig.BASE_ORDER_SIZE,
                    level_price,
                    self.symbol
                )
            else:
                side = SIDE_SELL
                # For sell orders, we need to have the asset
                balance = self.get_balance(self.symbol.replace('USDT', ''))
                order_size = min(
                    calculate_order_size(GridConfig.BASE_ORDER_SIZE, level_price, self.symbol),
                    balance
                )
            
            if order_size <= 0:
                continue
            
            # Format price and quantity
            formatted_price = format_price(level_price, self.symbol)
            formatted_quantity = format_quantity(order_size, self.symbol)
            
            # Validate order parameters
            is_valid, error_msg = validate_order_parameters(
                self.symbol, formatted_quantity, formatted_price
            )
            
            if not is_valid:
                logger.warning(f"Invalid order parameters for level {i}: {error_msg}")
                continue
            
            try:
                if Config.PAPER_TRADING:
                    # Simulate order placement
                    order = {
                        'symbol': self.symbol,
                        'orderId': f"paper_{i}_{get_current_timestamp()}",
                        'price': formatted_price,
                        'origQty': formatted_quantity,
                        'executedQty': '0',
                        'status': 'NEW',
                        'side': side,
                        'type': 'LIMIT',
                        'time': get_current_timestamp()
                    }
                    logger.info(f"Paper trading: Placed {side} order at {formatted_price}")
                else:
                    # Place real order
                    order = self.client.create_order(
                        symbol=self.symbol,
                        side=side,
                        type=ORDER_TYPE_LIMIT,
                        timeInForce=TIME_IN_FORCE_GTC,
                        quantity=formatted_quantity,
                        price=formatted_price
                    )
                    logger.info(f"Placed {side} order at {formatted_price}")
                
                placed_orders[order['orderId']] = {
                    'order': order,
                    'grid_level': level_price,
                    'level_index': i
                }
                
            except BinanceAPIException as e:
                logger.error(f"Failed to place order at level {i}: {e}")
                continue
        
        self.active_orders.update(placed_orders)
        logger.info(f"Placed {len(placed_orders)} grid orders")
        return placed_orders
    
    @retry_on_error
    def get_open_orders(self) -> List[Dict[str, Any]]:
        """Get all open orders for the trading pair."""
        if Config.PAPER_TRADING:
            return [order['order'] for order in self.active_orders.values()]
        
        orders = self.client.get_open_orders(symbol=self.symbol)
        return orders
    
    def check_order_status(self):
        """Check status of all active orders and handle executions."""
        open_orders = self.get_open_orders()
        open_order_ids = {order['orderId'] for order in open_orders}
        
        # Check for filled orders
        orders_to_remove = []
        for order_id, order_info in self.active_orders.items():
            if order_id not in open_order_ids:
                # Order was filled or cancelled
                if Config.PAPER_TRADING:
                    # Simulate order fill
                    order = order_info['order']
                    order['status'] = 'FILLED'
                    order['executedQty'] = order['origQty']
                    order['fills'] = [{
                        'price': order['price'],
                        'qty': order['origQty'],
                        'commission': '0'
                    }]
                
                self._handle_order_fill(order_info)
                orders_to_remove.append(order_id)
        
        # Remove filled orders from active orders
        for order_id in orders_to_remove:
            del self.active_orders[order_id]
    
    def _handle_order_fill(self, order_info: Dict[str, Any]):
        """Handle order fill and place opposite order."""
        order = order_info['order']
        grid_level = order_info['grid_level']
        
        # Log the trade execution
        log_trade_execution(order, grid_level)
        
        # Add to executed orders
        self.executed_orders.append({
            'order': order,
            'grid_level': grid_level,
            'timestamp': get_current_timestamp()
        })
        
        # Place opposite order at the next grid level
        self._place_opposite_order(order, grid_level)
    
    def _place_opposite_order(self, filled_order: Dict[str, Any], grid_level: float):
        """Place opposite order at the next grid level."""
        current_side = filled_order['side']
        opposite_side = SIDE_SELL if current_side == SIDE_BUY else SIDE_BUY
        
        # Find next grid level
        current_index = self.grid_levels.index(grid_level)
        if current_side == SIDE_BUY:
            # Buy order filled, place sell order at next higher level
            if current_index < len(self.grid_levels) - 1:
                next_level = self.grid_levels[current_index + 1]
            else:
                return  # No higher level available
        else:
            # Sell order filled, place buy order at next lower level
            if current_index > 0:
                next_level = self.grid_levels[current_index - 1]
            else:
                return  # No lower level available
        
        # Calculate order size
        order_size = calculate_order_size(
            GridConfig.BASE_ORDER_SIZE,
            next_level,
            self.symbol
        )
        
        if order_size <= 0:
            return
        
        # Format price and quantity
        formatted_price = format_price(next_level, self.symbol)
        formatted_quantity = format_quantity(order_size, self.symbol)
        
        try:
            if Config.PAPER_TRADING:
                # Simulate order placement
                new_order = {
                    'symbol': self.symbol,
                    'orderId': f"paper_opposite_{get_current_timestamp()}",
                    'price': formatted_price,
                    'origQty': formatted_quantity,
                    'executedQty': '0',
                    'status': 'NEW',
                    'side': opposite_side,
                    'type': 'LIMIT',
                    'time': get_current_timestamp()
                }
                logger.info(f"Paper trading: Placed opposite {opposite_side} order at {formatted_price}")
            else:
                # Place real order
                new_order = self.client.create_order(
                    symbol=self.symbol,
                    side=opposite_side,
                    type=ORDER_TYPE_LIMIT,
                    timeInForce=TIME_IN_FORCE_GTC,
                    quantity=formatted_quantity,
                    price=formatted_price
                )
                logger.info(f"Placed opposite {opposite_side} order at {formatted_price}")
            
            # Add to active orders
            self.active_orders[new_order['orderId']] = {
                'order': new_order,
                'grid_level': next_level,
                'level_index': self.grid_levels.index(next_level)
            }
            
        except BinanceAPIException as e:
            logger.error(f"Failed to place opposite order: {e}")
    
    def rebalance_grid(self):
        """Rebalance grid based on current market conditions."""
        if not GridConfig.AUTO_REBALANCE:
            return
            
        current_price = self.get_current_price()
        current_time = datetime.now()
        
        # Check if rebalancing is needed
        if (self.last_rebalance and 
            (current_time - self.last_rebalance).seconds < GridConfig.REBALANCE_INTERVAL):
            return
        
        logger.info("Rebalancing grid...")
        
        # Cancel all open orders
        self._cancel_all_orders()
        
        # Recalculate grid levels
        self.calculate_initial_grid()
        
        # Place new grid orders
        self.place_grid_orders()
        
        self.last_rebalance = current_time
        logger.info("Grid rebalancing completed")
    
    @retry_on_error
    def _cancel_all_orders(self):
        """Cancel all open orders."""
        if Config.PAPER_TRADING:
            self.active_orders.clear()
            logger.info("Paper trading: Cancelled all orders")
            return
        
        try:
            result = self.client.cancel_open_orders(symbol=self.symbol)
            self.active_orders.clear()
            logger.info(f"Cancelled {len(result)} open orders")
        except BinanceAPIException as e:
            logger.error(f"Failed to cancel orders: {e}")
    
    def calculate_performance(self) -> Dict[str, Any]:
        """Calculate bot performance metrics."""
        total_trades = len(self.executed_orders)
        total_volume = sum(
            float(order['order']['origQty']) * float(order['order']['price'])
            for order in self.executed_orders
        )
        
        # Calculate PnL (simplified)
        total_pnl = 0.0
        for order_data in self.executed_orders:
            order = order_data['order']
            if order['side'] == SIDE_BUY:
                # This is a simplified PnL calculation
                # In a real implementation, you'd track positions more carefully
                pass
        
        return {
            'total_trades': total_trades,
            'total_volume': total_volume,
            'total_pnl': total_pnl,
            'active_orders': len(self.active_orders),
            'uptime': (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
        }
    
    def print_status(self):
        """Print current bot status."""
        performance = self.calculate_performance()
        current_price = self.get_current_price()
        
        print("\n" + "="*50)
        print("GRID TRADING BOT STATUS")
        print("="*50)
        print(f"Symbol: {self.symbol}")
        print(f"Current Price: {current_price}")
        print(f"Active Orders: {performance['active_orders']}")
        print(f"Total Trades: {performance['total_trades']}")
        print(f"Total Volume: {performance['total_volume']:.2f} USDT")
        print(f"Uptime: {performance['uptime']:.0f} seconds")
        print("="*50)
    
    def run(self):
        """Main bot loop."""
        if not Config.validate_config() or not GridConfig.validate_config():
            logger.error("Invalid configuration. Please check your settings.")
            return
        
        logger.info("Starting Grid Trading Bot...")
        Config.print_config()
        GridConfig.print_config()
        
        self.is_running = True
        self.start_time = datetime.now()
        
        try:
            # Initialize grid
            self.calculate_initial_grid()
            self.place_grid_orders()
            
            logger.info("Grid Trading Bot is running. Press Ctrl+C to stop.")
            
            while self.is_running:
                try:
                    # Check order status
                    self.check_order_status()
                    
                    # Rebalance grid periodically
                    self.rebalance_grid()
                    
                    # Print status every 60 seconds
                    if int(time.time()) % 60 == 0:
                        self.print_status()
                    
                    # Sleep for a short interval
                    time.sleep(Config.REQUEST_DELAY)
                    
                except KeyboardInterrupt:
                    logger.info("Received interrupt signal. Stopping bot...")
                    break
                except Exception as e:
                    logger.error(f"Error in main loop: {e}")
                    time.sleep(5)  # Wait before retrying
        
        finally:
            self.stop()
    
    def stop(self):
        """Stop the bot and clean up."""
        logger.info("Stopping Grid Trading Bot...")
        self.is_running = False
        
        # Cancel all open orders
        self._cancel_all_orders()
        
        # Print final performance
        self.print_status()
        logger.info("Grid Trading Bot stopped.")

def main():
    """Main entry point."""
    try:
        bot = GridTradingBot()
        bot.run()
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 