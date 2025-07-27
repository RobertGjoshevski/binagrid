"""
Signal Trading Bot implementation.
Implements signal-based trading strategy using external signals.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'common'))

import time
import logging
import signal
import re
import json
import requests
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
from signal_config import SignalConfig

# Set up logging
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SignalTradingBot:
    """
    Signal Trading Bot class.
    Implements signal-based trading strategy using external signals.
    """
    
    def __init__(self):
        """Initialize the Signal Trading Bot."""
        self.client = None
        self.symbol = Config.TRADING_PAIR
        self.positions = []
        self.executed_orders = []
        self.active_signals = []
        self.is_running = False
        self.start_time = None
        self.signal_history = []
        self.total_pnl = 0.0
        
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
    
    def calculate_macd(self, prices: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, float]:
        """Calculate MACD (Moving Average Convergence Divergence)."""
        if len(prices) < slow + signal:
            return {'macd': 0, 'signal': 0, 'histogram': 0}
        
        # Calculate EMAs
        ema_fast = self._calculate_ema(prices, fast)
        ema_slow = self._calculate_ema(prices, slow)
        
        # Calculate MACD line
        macd_line = ema_fast - ema_slow
        
        # Calculate signal line (EMA of MACD)
        macd_values = [macd_line]  # Simplified - in reality you'd need full MACD history
        signal_line = self._calculate_ema(macd_values, signal)
        
        # Calculate histogram
        histogram = macd_line - signal_line
        
        return {
            'macd': macd_line,
            'signal': signal_line,
            'histogram': histogram
        }
    
    def _calculate_ema(self, prices: List[float], period: int) -> float:
        """Calculate Exponential Moving Average."""
        if len(prices) < period:
            return prices[-1] if prices else 0.0
        
        multiplier = 2 / (period + 1)
        ema = prices[0]
        
        for price in prices[1:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))
        
        return ema
    
    def check_technical_indicators(self, signal_type: str) -> bool:
        """Check if technical indicators confirm the signal."""
        if not SignalConfig.USE_TECHNICAL_CONFIRMATION:
            return True
        
        prices = self.get_historical_prices()
        if not prices:
            return True
        
        current_price = prices[-1]
        
        # Check RSI
        rsi = self.calculate_rsi(prices, 14)
        
        # Check MACD
        macd_data = self.calculate_macd(prices)
        
        # Signal confirmation logic
        if signal_type.upper() in ['BUY', 'LONG']:
            # Buy signals
            rsi_confirm = rsi <= SignalConfig.RSI_OVERBOUGHT  # Not overbought
            macd_confirm = macd_data['histogram'] > 0  # MACD histogram positive
            
            if 'RSI' in SignalConfig.REQUIRED_INDICATORS and not rsi_confirm:
                logger.info(f"RSI ({rsi:.2f}) doesn't confirm buy signal")
                return False
            
            if 'MACD' in SignalConfig.REQUIRED_INDICATORS and not macd_confirm:
                logger.info(f"MACD histogram ({macd_data['histogram']:.6f}) doesn't confirm buy signal")
                return False
        
        elif signal_type.upper() in ['SELL', 'SHORT']:
            # Sell signals
            rsi_confirm = rsi >= SignalConfig.RSI_OVERSOLD  # Not oversold
            macd_confirm = macd_data['histogram'] < 0  # MACD histogram negative
            
            if 'RSI' in SignalConfig.REQUIRED_INDICATORS and not rsi_confirm:
                logger.info(f"RSI ({rsi:.2f}) doesn't confirm sell signal")
                return False
            
            if 'MACD' in SignalConfig.REQUIRED_INDICATORS and not macd_confirm:
                logger.info(f"MACD histogram ({macd_data['histogram']:.6f}) doesn't confirm sell signal")
                return False
        
        logger.info(f"Technical indicators confirm {signal_type} signal")
        return True
    
    def check_market_conditions(self) -> bool:
        """Check if market conditions are suitable for trading."""
        if not SignalConfig.MARKET_FILTER:
            return True
        
        try:
            # Get 24h ticker statistics
            ticker_24h = self.client.get_ticker(symbol=self.symbol)
            
            # Check volume
            volume_24h = float(ticker_24h['volume']) * float(ticker_24h['lastPrice'])
            if volume_24h < SignalConfig.MIN_VOLUME_24H:
                logger.info(f"24h volume ({volume_24h:.0f}) below minimum ({SignalConfig.MIN_VOLUME_24H})")
                return False
            
            # Check spread (bid-ask spread)
            bid_price = float(ticker_24h['bidPrice'])
            ask_price = float(ticker_24h['askPrice'])
            spread_percent = ((ask_price - bid_price) / bid_price) * 100
            
            if spread_percent > SignalConfig.MAX_SPREAD_PERCENT:
                logger.info(f"Spread ({spread_percent:.2f}%) above maximum ({SignalConfig.MAX_SPREAD_PERCENT}%)")
                return False
            
            logger.info(f"Market conditions suitable: Volume={volume_24h:.0f}, Spread={spread_percent:.2f}%")
            return True
            
        except Exception as e:
            logger.error(f"Failed to check market conditions: {e}")
            return False
    
    def parse_signal_message(self, message: str) -> Optional[Dict[str, Any]]:
        """Parse signal message to extract trading information."""
        message = message.upper()
        
        # Check for signal keywords
        signal_type = None
        for signal_key, keywords in SignalConfig.SIGNAL_KEYWORDS.items():
            for keyword in keywords:
                if keyword.upper() in message:
                    signal_type = signal_key
                    break
            if signal_type:
                break
        
        if not signal_type:
            return None
        
        # Extract symbol (simplified - in reality you'd need more sophisticated parsing)
        symbol_match = re.search(r'([A-Z]{3,10})USDT', message)
        symbol = symbol_match.group(1) + 'USDT' if symbol_match else self.symbol
        
        # Extract price targets (simplified)
        price_matches = re.findall(r'(\d+\.?\d*)', message)
        entry_price = None
        target_price = None
        stop_loss = None
        
        if len(price_matches) >= 1:
            entry_price = float(price_matches[0])
        if len(price_matches) >= 2:
            target_price = float(price_matches[1])
        if len(price_matches) >= 3:
            stop_loss = float(price_matches[2])
        
        return {
            'type': signal_type,
            'symbol': symbol,
            'entry_price': entry_price,
            'target_price': target_price,
            'stop_loss': stop_loss,
            'message': message,
            'timestamp': get_current_timestamp()
        }
    
    def get_telegram_signals(self) -> List[Dict[str, Any]]:
        """Get signals from Telegram channels (placeholder implementation)."""
        # This is a placeholder - you would need to implement Telegram bot integration
        # For now, we'll return an empty list
        logger.info("Telegram signal fetching not implemented yet")
        return []
    
    def get_api_signals(self) -> List[Dict[str, Any]]:
        """Get signals from external APIs (placeholder implementation)."""
        signals = []
        
        for endpoint in SignalConfig.API_ENDPOINTS:
            if not endpoint:
                continue
            
            try:
                response = requests.get(endpoint, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    # Parse API response based on the specific API format
                    # This is a placeholder implementation
                    logger.info(f"API signal from {endpoint}: {data}")
            except Exception as e:
                logger.error(f"Failed to fetch signals from {endpoint}: {e}")
        
        return signals
    
    def collect_signals(self) -> List[Dict[str, Any]]:
        """Collect signals from all configured sources."""
        signals = []
        
        # Get signals from different sources
        if 'TELEGRAM' in SignalConfig.SIGNAL_SOURCES:
            telegram_signals = self.get_telegram_signals()
            signals.extend(telegram_signals)
        
        if 'API' in SignalConfig.SIGNAL_SOURCES:
            api_signals = self.get_api_signals()
            signals.extend(api_signals)
        
        return signals
    
    def validate_signal(self, signal: Dict[str, Any]) -> bool:
        """Validate a trading signal."""
        # Check if signal type is supported
        if signal['type'] not in SignalConfig.SUPPORTED_SIGNALS:
            logger.info(f"Unsupported signal type: {signal['type']}")
            return False
        
        # Check if symbol matches our trading pair
        if signal['symbol'] != self.symbol:
            logger.info(f"Signal symbol ({signal['type']}) doesn't match trading pair ({self.symbol})")
            return False
        
        # Check market conditions
        if not self.check_market_conditions():
            return False
        
        # Check technical indicators
        if not self.check_technical_indicators(signal['type']):
            return False
        
        return True
    
    def calculate_position_size(self) -> float:
        """Calculate position size based on portfolio percentage."""
        account = self.get_account_info()
        total_balance = 0.0
        
        # Calculate total USDT balance
        for balance in account['balances']:
            if balance['asset'] == 'USDT':
                total_balance = float(balance['free'])
                break
        
        position_size = total_balance * (SignalConfig.POSITION_SIZE_PERCENT / 100)
        return min(position_size, total_balance)  # Don't exceed available balance
    
    @retry_on_error
    def execute_signal(self, signal: Dict[str, Any]) -> bool:
        """Execute a trading signal."""
        if not self.validate_signal(signal):
            return False
        
        # Check if we have too many positions
        if len(self.positions) >= SignalConfig.MAX_POSITIONS:
            logger.info(f"Maximum positions reached ({SignalConfig.MAX_POSITIONS})")
            return False
        
        current_price = self.get_current_price()
        position_size = self.calculate_position_size()
        
        if position_size <= 0:
            logger.warning("Insufficient balance for position")
            return False
        
        # Determine order side
        if signal['type'] in ['BUY', 'LONG']:
            side = SIDE_BUY
        elif signal['type'] in ['SELL', 'SHORT']:
            side = SIDE_SELL
        else:
            logger.error(f"Unknown signal type: {signal['type']}")
            return False
        
        # Calculate quantity
        quantity = position_size / current_price
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
                    'orderId': f"signal_paper_{get_current_timestamp()}",
                    'price': current_price,
                    'origQty': formatted_quantity,
                    'executedQty': formatted_quantity,
                    'status': 'FILLED',
                    'side': side,
                    'type': 'MARKET',
                    'time': get_current_timestamp(),
                    'fills': [{
                        'price': current_price,
                        'qty': formatted_quantity,
                        'commission': '0'
                    }]
                }
                logger.info(f"Paper trading: Signal {side} {formatted_quantity} {self.symbol} @ {current_price}")
            else:
                # Place real order
                order = self.client.create_order(
                    symbol=self.symbol,
                    side=side,
                    type=ORDER_TYPE_MARKET,
                    quantity=formatted_quantity
                )
                logger.info(f"Signal executed: {side} {formatted_quantity} {self.symbol} @ {current_price}")
            
            # Update tracking
            self.executed_orders.append({
                'order': order,
                'signal': signal,
                'timestamp': get_current_timestamp()
            })
            
            # Add to positions
            self.positions.append({
                'order': order,
                'signal': signal,
                'entry_price': current_price,
                'target_price': signal.get('target_price'),
                'stop_loss': signal.get('stop_loss'),
                'timestamp': get_current_timestamp()
            })
            
            # Log the trade
            log_trade_execution(order, current_price)
            
            return True
            
        except BinanceAPIException as e:
            logger.error(f"Failed to execute signal: {e}")
            return False
    
    def check_signal_timeout(self):
        """Check for signal timeouts and remove old signals."""
        current_time = get_current_timestamp()
        timeout_ms = SignalConfig.SIGNAL_TIMEOUT * 1000
        
        # Remove old signals
        self.active_signals = [
            signal for signal in self.active_signals
            if (current_time - signal['timestamp']) < timeout_ms
        ]
    
    def process_signals(self):
        """Process incoming signals."""
        # Collect new signals
        new_signals = self.collect_signals()
        
        # Add to active signals
        for signal in new_signals:
            if signal not in self.active_signals:
                self.active_signals.append(signal)
                logger.info(f"New signal received: {signal['type']} {signal['symbol']}")
        
        # Check signal confirmation
        signal_counts = {}
        for signal in self.active_signals:
            key = f"{signal['type']}_{signal['symbol']}"
            signal_counts[key] = signal_counts.get(key, 0) + 1
        
        # Execute confirmed signals
        for key, count in signal_counts.items():
            if count >= SignalConfig.SIGNAL_CONFIRMATION:
                # Get the first signal of this type
                signal = next(s for s in self.active_signals if f"{s['type']}_{s['symbol']}" == key)
                
                # Execute the signal
                if self.execute_signal(signal):
                    # Remove all signals of this type
                    self.active_signals = [s for s in self.active_signals if f"{s['type']}_{s['symbol']}" != key]
    
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
            'active_positions': len(self.positions),
            'active_signals': len(self.active_signals),
            'uptime': (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
        }
    
    def print_status(self):
        """Print current bot status."""
        performance = self.calculate_performance()
        current_price = self.get_current_price()
        
        print("\n" + "="*50)
        print("SIGNAL TRADING BOT STATUS")
        print("="*50)
        print(f"Symbol: {self.symbol}")
        print(f"Current Price: {current_price}")
        print(f"Active Positions: {performance['active_positions']}")
        print(f"Active Signals: {performance['active_signals']}")
        print(f"Total Trades: {performance['total_trades']}")
        print(f"Total Volume: {performance['total_volume']:.2f} USDT")
        print(f"Uptime: {performance['uptime']:.0f} seconds")
        print("="*50)
    
    def run(self):
        """Main bot loop."""
        if not Config.validate_config() or not SignalConfig.validate_config():
            logger.error("Invalid configuration. Please check your settings.")
            return
        
        logger.info("Starting Signal Trading Bot...")
        Config.print_config()
        SignalConfig.print_config()
        
        self.is_running = True
        self.start_time = datetime.now()
        
        try:
            logger.info("Signal Trading Bot is running. Press Ctrl+C to stop.")
            
            while self.is_running:
                try:
                    # Process signals
                    self.process_signals()
                    
                    # Check signal timeouts
                    self.check_signal_timeout()
                    
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
        logger.info("Stopping Signal Trading Bot...")
        self.is_running = False
        
        # Print final performance
        self.print_status()
        logger.info("Signal Trading Bot stopped.")

def main():
    """Main entry point."""
    try:
        bot = SignalTradingBot()
        bot.run()
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 