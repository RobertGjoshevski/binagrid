"""
Common configuration settings for all trading bots.
Handles API keys, common trading parameters, and shared configuration.
"""

import os
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv('.env')

class Config:
    """Common configuration class for all trading bots."""
    
    # Binance API Configuration
    BINANCE_API_KEY = os.getenv('BINANCE_API_KEY')
    BINANCE_SECRET_KEY = os.getenv('BINANCE_SECRET_KEY')
    BINANCE_TESTNET = os.getenv('BINANCE_TESTNET', 'True').lower() == 'true'
    
    # Common Trading Configuration
    TRADING_PAIR = os.getenv('TRADING_PAIR', 'BTCUSDT')
    BASE_ORDER_SIZE = float(os.getenv('BASE_ORDER_SIZE', '10.0'))  # Default order size
    
    # Risk Management (Common)
    STOP_LOSS_PERCENT = float(os.getenv('STOP_LOSS_PERCENT', '5.0'))
    TAKE_PROFIT_PERCENT = float(os.getenv('TAKE_PROFIT_PERCENT', '10.0'))
    MAX_DAILY_LOSS = float(os.getenv('MAX_DAILY_LOSS', '100.0'))  # USDT
    
    # Bot Behavior (Common)
    ENABLE_LOGGING = os.getenv('ENABLE_LOGGING', 'True').lower() == 'true'
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    PAPER_TRADING = os.getenv('PAPER_TRADING', 'True').lower() == 'true'
    
    # API Rate Limiting
    MAX_REQUESTS_PER_MINUTE = int(os.getenv('MAX_REQUESTS_PER_MINUTE', '1200'))
    REQUEST_DELAY = float(os.getenv('REQUEST_DELAY', '0.1'))  # seconds
    
    # Database and Storage
    ENABLE_DATABASE = os.getenv('ENABLE_DATABASE', 'False').lower() == 'true'
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///trading_bot.db')
    
    # Notifications
    ENABLE_NOTIFICATIONS = os.getenv('ENABLE_NOTIFICATIONS', 'False').lower() == 'true'
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')
    
    @classmethod
    def validate_config(cls) -> bool:
        """Validate common configuration settings."""
        if not cls.BINANCE_API_KEY or not cls.BINANCE_SECRET_KEY:
            print("ERROR: BINANCE_API_KEY and BINANCE_SECRET_KEY must be set in .env file")
            return False
        
        if cls.BASE_ORDER_SIZE <= 0:
            print("ERROR: BASE_ORDER_SIZE must be greater than 0")
            return False
        
        if cls.STOP_LOSS_PERCENT <= 0:
            print("ERROR: STOP_LOSS_PERCENT must be greater than 0")
            return False
        
        return True
    
    @classmethod
    def get_binance_config(cls) -> Dict[str, Any]:
        """Get Binance API configuration."""
        config = {
            'api_key': cls.BINANCE_API_KEY,
            'api_secret': cls.BINANCE_SECRET_KEY,
        }
        
        if cls.BINANCE_TESTNET:
            config['testnet'] = True
            config['base_url'] = 'https://testnet.binance.vision'
        
        return config
    
    @classmethod
    def print_config(cls) -> None:
        """Print common configuration (without sensitive data)."""
        print("=== Common Bot Configuration ===")
        print(f"Trading Pair: {cls.TRADING_PAIR}")
        print(f"Base Order Size: {cls.BASE_ORDER_SIZE} USDT")
        print(f"Stop Loss: {cls.STOP_LOSS_PERCENT}%")
        print(f"Take Profit: {cls.TAKE_PROFIT_PERCENT}%")
        print(f"Max Daily Loss: {cls.MAX_DAILY_LOSS} USDT")
        print(f"Testnet Mode: {cls.BINANCE_TESTNET}")
        print(f"Paper Trading: {cls.PAPER_TRADING}")
        print(f"Logging: {cls.ENABLE_LOGGING}")
        print(f"Database: {cls.ENABLE_DATABASE}")
        print(f"Notifications: {cls.ENABLE_NOTIFICATIONS}")
        print("=================================")

# Trading pair specific configurations
TRADING_PAIRS_CONFIG = {
    'BTCUSDT': {
        'min_qty': 0.00001,
        'step_size': 0.00001,
        'price_precision': 2,
        'quantity_precision': 5,
    },
    'ETHUSDT': {
        'min_qty': 0.001,
        'step_size': 0.001,
        'price_precision': 2,
        'quantity_precision': 3,
    },
    'ADAUSDT': {
        'min_qty': 1,
        'step_size': 1,
        'price_precision': 4,
        'quantity_precision': 0,
    },
    'DEFAULT': {
        'min_qty': 0.001,
        'step_size': 0.001,
        'price_precision': 2,
        'quantity_precision': 3,
    }
}

def get_trading_pair_config(symbol: str) -> Dict[str, Any]:
    """Get configuration for a specific trading pair."""
    return TRADING_PAIRS_CONFIG.get(symbol, TRADING_PAIRS_CONFIG['DEFAULT']) 