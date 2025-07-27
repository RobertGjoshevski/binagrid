"""
DCA (Dollar Cost Averaging) Trading Bot implementation.
Implements DCA strategy using Binance API.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'common'))

import time
import logging
import signal
import schedule
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from binance.client import Client
from binance.exceptions import BinanceAPIException
from binance.enums import *
import pandas as pd
import numpy as np

from config import Config, get_trading_pair_config
from utils import (
    format_quantity,
    format_price,
    calculate_order_size,
    validate_order_parameters,
    retry_on_error,
    log_trade_execution,
    calculate_pnl,
    get_current_timestamp
)
from dca_config import DCAConfig

# Set up logging
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DCATradingBot:
    """
    DCA Trading Bot class.
    Implements Dollar Cost Averaging strategy with dip buying.
    """
    
    def __init__(self):
        """Initialize the DCA Trading Bot."""
        self.client = None
        self.symbol = Config.TRADING_PAIR
        self.positions = []
        self.executed_orders = []
        self.is_running = False
        self.start_time = None
        self.daily_dca_count = 0
        self.last_dca_date = None
        self.total_invested = 0.0
        self.price_history = []
        
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
    
    def get_historical_prices(self, interval: str = '1h', limit: int = 24) -> List[float]:
        """Get historical price data for technical analysis."""
        try:
            klines = self.client.get_klines(
                symbol=self.symbol,
                interval=interval,
                limit=limit
            )
            prices = [float(kline[4]) for kline in klines]  # Close prices
            return prices
        except Exception as e:
            logger.error(f"Failed to get historical prices: {e}")
            return []
    
    def calculate_rsi(self, prices: List[float], period: int = 14) -> float:
        """Calculate RSI (Relative Strength Index)."""
        if len(prices) < period + 1:
            return 50.0  # Neutral RSI if not enough data
        
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def calculate_moving_average(self, prices: List[float], period: int = 20) -> float:
        """Calculate Simple Moving Average."""
        if len(prices) < period:
            return prices[-1] if prices else 0.0
        
        return np.mean(prices[-period:])
    
    def should_buy_on_dip(self, current_price: float) -> bool:
        """Determine if we should buy on a dip."""
        if not DCAConfig.DCA_ON_DIP:
            return False
        
        # Get historical prices
        prices = self.get_historical_prices()
        if not prices:
            return False
        
        # Calculate price drop percentage
        recent_high = max(prices[-7:])  # Last 7 hours
        price_drop = ((recent_high - current_price) / recent_high) * 100
        
        # Check if price dropped enough to trigger extra DCA
        if price_drop >= DCAConfig.DIP_THRESHOLD:
            logger.info(f"Price dropped {price_drop:.2f}% from recent high. Triggering dip buy.")
            return True
        
        return False
    
    def should_buy_technically(self, current_price: float) -> bool:
        """Check if technical indicators suggest buying."""
        if not DCAConfig.USE_TECHNICAL_INDICATORS:
            return True
        
        prices = self.get_historical_prices()
        if not prices:
            return True
        
        # Calculate RSI
        rsi = self.calculate_rsi(prices, 14)
        
        # Calculate Moving Average
        ma = self.calculate_moving_average(prices, DCAConfig.MA_PERIOD)
        
        # Buy conditions
        rsi_oversold = rsi <= DCAConfig.RSI_OVERSOLD
        price_below_ma = current_price < ma
        
        if rsi_oversold or price_below_ma:
            logger.info(f"Technical buy signal: RSI={rsi:.2f}, Price={current_price:.2f}, MA={ma:.2f}")
            return True
        
        return False
    
    def can_execute_dca(self) -> bool:
        """Check if we can execute DCA based on limits."""
        current_date = datetime.now().date()
        
        # Reset daily counter if it's a new day
        if self.last_dca_date != current_date:
            self.daily_dca_count = 0
            self.last_dca_date = current_date
        
        # Check daily limit
        if self.daily_dca_count >= DCAConfig.MAX_DCA_PER_DAY:
            logger.info(f"Daily DCA limit reached ({DCAConfig.MAX_DCA_PER_DAY})")
            return False
        
        # Check total investment limit
        if self.total_invested >= DCAConfig.MAX_TOTAL_INVESTMENT:
            logger.info(f"Total investment limit reached ({DCAConfig.MAX_TOTAL_INVESTMENT} USDT)")
            return False
        
        return True
    
    def calculate_dca_amount(self, is_dip_buy: bool = False) -> float:
        """Calculate the DCA amount for this purchase."""
        base_amount = DCAConfig.DCA_AMOUNT
        
        if is_dip_buy and DCAConfig.DCA_ON_DIP:
            base_amount *= DCAConfig.EXTRA_DCA_MULTIPLIER
            logger.info(f"Dip buy detected. Increasing amount to {base_amount} USDT")
        
        return base_amount
    
    @retry_on_error
    def execute_dca_purchase(self, amount: float, reason: str = "Scheduled DCA"):
        """Execute a DCA purchase."""
        if not self.can_execute_dca():
            return False
        
        current_price = self.get_current_price()
        
        # Check technical indicators
        if not self.should_buy_technically(current_price):
            logger.info("Technical indicators don't support buying. Skipping DCA.")
            return False
        
        # Calculate quantity
        quantity = amount / current_price
        formatted_quantity = format_quantity(quantity, self.symbol)
        
        # Validate order parameters
        is_valid, error_msg = validate_order_parameters(
            self.symbol, formatted_quantity, current_price
        )
        
        if not is_valid:
            logger.warning(f"Invalid order parameters: {error_msg}")
            return False
        
        try:
            if Config.PAPER_TRADING:
                # Simulate order placement
                order = {
                    'symbol': self.symbol,
                    'orderId': f"dca_paper_{get_current_timestamp()}",
                    'price': current_price,
                    'origQty': formatted_quantity,
                    'executedQty': formatted_quantity,
                    'status': 'FILLED',
                    'side': SIDE_BUY,
                    'type': 'MARKET',
                    'time': get_current_timestamp(),
                    'fills': [{
                        'price': current_price,
                        'qty': formatted_quantity,
                        'commission': '0'
                    }]
                }
                logger.info(f"Paper trading: DCA purchase {formatted_quantity} {self.symbol} @ {current_price}")
            else:
                # Place real order
                order = self.client.create_order(
                    symbol=self.symbol,
                    side=SIDE_BUY,
                    type=ORDER_TYPE_MARKET,
                    quantity=formatted_quantity
                )
                logger.info(f"DCA purchase executed: {formatted_quantity} {self.symbol} @ {current_price}")
            
            # Update tracking
            self.executed_orders.append({
                'order': order,
                'reason': reason,
                'timestamp': get_current_timestamp()
            })
            
            self.daily_dca_count += 1
            self.total_invested += amount
            
            # Log the trade
            log_trade_execution(order, current_price)
            
            return True
            
        except BinanceAPIException as e:
            logger.error(f"Failed to execute DCA purchase: {e}")
            return False
    
    def scheduled_dca(self):
        """Execute scheduled DCA purchase."""
        logger.info("Executing scheduled DCA purchase...")
        self.execute_dca_purchase(DCAConfig.DCA_AMOUNT, "Scheduled DCA")
    
    def check_dip_opportunities(self):
        """Check for dip buying opportunities."""
        current_price = self.get_current_price()
        
        if self.should_buy_on_dip(current_price):
            dip_amount = self.calculate_dca_amount(is_dip_buy=True)
            self.execute_dca_purchase(dip_amount, "Dip Buy")
    
    def setup_schedule(self):
        """Setup DCA schedule based on configuration."""
        if not DCAConfig.ENABLE_SCHEDULING:
            return
        
        schedule_time = DCAConfig.DCA_TIME
        
        if DCAConfig.DCA_INTERVAL == 'DAILY':
            schedule.every().day.at(schedule_time).do(self.scheduled_dca)
            logger.info(f"Scheduled daily DCA at {schedule_time}")
        elif DCAConfig.DCA_INTERVAL == 'WEEKLY':
            schedule.every().monday.at(schedule_time).do(self.scheduled_dca)
            logger.info(f"Scheduled weekly DCA on Monday at {schedule_time}")
        elif DCAConfig.DCA_INTERVAL == 'MONTHLY':
            schedule.every().month.at(schedule_time).do(self.scheduled_dca)
            logger.info(f"Scheduled monthly DCA at {schedule_time}")
    
    def calculate_performance(self) -> Dict[str, Any]:
        """Calculate bot performance metrics."""
        total_trades = len(self.executed_orders)
        total_volume = sum(
            float(order['order']['origQty']) * float(order['order']['price'])
            for order in self.executed_orders
        )
        
        # Calculate average purchase price
        if total_trades > 0:
            total_quantity = sum(float(order['order']['origQty']) for order in self.executed_orders)
            avg_price = total_volume / total_quantity if total_quantity > 0 else 0
        else:
            avg_price = 0
        
        current_price = self.get_current_price()
        current_value = total_volume if total_trades == 0 else (total_quantity * current_price)
        unrealized_pnl = current_value - self.total_invested
        
        return {
            'total_trades': total_trades,
            'total_invested': self.total_invested,
            'total_volume': total_volume,
            'avg_price': avg_price,
            'current_price': current_price,
            'unrealized_pnl': unrealized_pnl,
            'daily_dca_count': self.daily_dca_count,
            'uptime': (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
        }
    
    def print_status(self):
        """Print current bot status."""
        performance = self.calculate_performance()
        
        print("\n" + "="*50)
        print("DCA TRADING BOT STATUS")
        print("="*50)
        print(f"Symbol: {self.symbol}")
        print(f"Current Price: {performance['current_price']:.2f}")
        print(f"Total Trades: {performance['total_trades']}")
        print(f"Total Invested: {performance['total_invested']:.2f} USDT")
        print(f"Average Price: {performance['avg_price']:.2f}")
        print(f"Unrealized PnL: {performance['unrealized_pnl']:.2f} USDT")
        print(f"Daily DCA Count: {performance['daily_dca_count']}/{DCAConfig.MAX_DCA_PER_DAY}")
        print(f"Uptime: {performance['uptime']:.0f} seconds")
        print("="*50)
    
    def run(self):
        """Main bot loop."""
        if not Config.validate_config() or not DCAConfig.validate_config():
            logger.error("Invalid configuration. Please check your settings.")
            return
        
        logger.info("Starting DCA Trading Bot...")
        Config.print_config()
        DCAConfig.print_config()
        
        self.is_running = True
        self.start_time = datetime.now()
        
        # Setup schedule
        self.setup_schedule()
        
        try:
            logger.info("DCA Trading Bot is running. Press Ctrl+C to stop.")
            
            while self.is_running:
                try:
                    # Run scheduled tasks
                    schedule.run_pending()
                    
                    # Check for dip opportunities
                    self.check_dip_opportunities()
                    
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
        logger.info("Stopping DCA Trading Bot...")
        self.is_running = False
        
        # Print final performance
        self.print_status()
        logger.info("DCA Trading Bot stopped.")

def main():
    """Main entry point."""
    try:
        bot = DCATradingBot()
        bot.run()
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 