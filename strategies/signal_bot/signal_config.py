"""
Signal Trading Bot Configuration
Specific settings for signal-based trading strategy.
"""

import os
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv('../common/.env')

class SignalConfig:
    """Configuration class for the Signal Trading Bot."""
    
    # Bot Identity
    BOT_NAME = "Signal Trading Bot"
    BOT_TYPE = "SIGNAL"
    
    # Signal Sources
    SIGNAL_SOURCES = os.getenv('SIGNAL_SOURCES', 'TELEGRAM,API').split(',')
    TELEGRAM_CHANNELS = os.getenv('TELEGRAM_CHANNELS', '').split(',')  # Channel usernames
    API_ENDPOINTS = os.getenv('API_ENDPOINTS', '').split(',')  # External API endpoints
    
    # Signal Processing
    SIGNAL_CONFIRMATION = int(os.getenv('SIGNAL_CONFIRMATION', '2'))  # Number of sources to confirm
    SIGNAL_TIMEOUT = int(os.getenv('SIGNAL_TIMEOUT', '300'))  # Seconds to wait for signal execution
    MIN_SIGNAL_STRENGTH = float(os.getenv('MIN_SIGNAL_STRENGTH', '0.7'))  # 0-1 scale
    
    # Trading Parameters
    POSITION_SIZE_PERCENT = float(os.getenv('POSITION_SIZE_PERCENT', '10.0'))  # % of portfolio per trade
    MAX_POSITIONS = int(os.getenv('MAX_POSITIONS', '5'))  # Maximum concurrent positions
    LEVERAGE = float(os.getenv('LEVERAGE', '1.0'))  # Trading leverage (1.0 = spot)
    
    # Risk Management
    STOP_LOSS_PERCENT = float(os.getenv('STOP_LOSS_PERCENT', '5.0'))
    TAKE_PROFIT_PERCENT = float(os.getenv('TAKE_PROFIT_PERCENT', '10.0'))
    TRAILING_STOP = os.getenv('TRAILING_STOP', 'True').lower() == 'true'
    TRAILING_STOP_PERCENT = float(os.getenv('TRAILING_STOP_PERCENT', '2.0'))
    
    # Signal Types
    SUPPORTED_SIGNALS = os.getenv('SUPPORTED_SIGNALS', 'BUY,SELL,LONG,SHORT').split(',')
    SIGNAL_KEYWORDS = {
        'BUY': os.getenv('BUY_KEYWORDS', 'buy,long,bullish,accumulate').split(','),
        'SELL': os.getenv('SELL_KEYWORDS', 'sell,short,bearish,exit').split(','),
        'STOP': os.getenv('STOP_KEYWORDS', 'stop,close,exit,cut').split(',')
    }
    
    # Technical Analysis
    USE_TECHNICAL_CONFIRMATION = os.getenv('USE_TECHNICAL_CONFIRMATION', 'True').lower() == 'true'
    REQUIRED_INDICATORS = os.getenv('REQUIRED_INDICATORS', 'RSI,MACD').split(',')
    
    # Market Conditions
    MARKET_FILTER = os.getenv('MARKET_FILTER', 'True').lower() == 'true'
    MIN_VOLUME_24H = float(os.getenv('MIN_VOLUME_24H', '1000000'))  # Minimum 24h volume
    MAX_SPREAD_PERCENT = float(os.getenv('MAX_SPREAD_PERCENT', '1.0'))  # Maximum spread
    
    # Performance Tracking
    TRACK_PERFORMANCE = os.getenv('TRACK_PERFORMANCE', 'True').lower() == 'true'
    PERFORMANCE_METRICS = os.getenv('PERFORMANCE_METRICS', 'WIN_RATE,PROFIT_FACTOR,SHARPE_RATIO').split(',')
    
    @classmethod
    def validate_config(cls) -> bool:
        """Validate signal-specific configuration."""
        if cls.POSITION_SIZE_PERCENT <= 0 or cls.POSITION_SIZE_PERCENT > 100:
            print("ERROR: POSITION_SIZE_PERCENT must be between 0 and 100")
            return False
        
        if cls.MAX_POSITIONS <= 0:
            print("ERROR: MAX_POSITIONS must be greater than 0")
            return False
        
        if cls.SIGNAL_CONFIRMATION <= 0:
            print("ERROR: SIGNAL_CONFIRMATION must be greater than 0")
            return False
        
        if cls.MIN_SIGNAL_STRENGTH < 0 or cls.MIN_SIGNAL_STRENGTH > 1:
            print("ERROR: MIN_SIGNAL_STRENGTH must be between 0 and 1")
            return False
        
        if cls.STOP_LOSS_PERCENT <= 0:
            print("ERROR: STOP_LOSS_PERCENT must be greater than 0")
            return False
        
        return True
    
    @classmethod
    def print_config(cls) -> None:
        """Print signal-specific configuration."""
        print("=== Signal Trading Bot Configuration ===")
        print(f"Signal Sources: {', '.join(cls.SIGNAL_SOURCES)}")
        print(f"Signal Confirmation: {cls.SIGNAL_CONFIRMATION} sources")
        print(f"Signal Timeout: {cls.SIGNAL_TIMEOUT} seconds")
        print(f"Min Signal Strength: {cls.MIN_SIGNAL_STRENGTH}")
        print(f"Position Size: {cls.POSITION_SIZE_PERCENT}%")
        print(f"Max Positions: {cls.MAX_POSITIONS}")
        print(f"Leverage: {cls.LEVERAGE}x")
        print(f"Stop Loss: {cls.STOP_LOSS_PERCENT}%")
        print(f"Take Profit: {cls.TAKE_PROFIT_PERCENT}%")
        print(f"Trailing Stop: {cls.TRAILING_STOP}")
        if cls.TRAILING_STOP:
            print(f"Trailing Stop %: {cls.TRAILING_STOP_PERCENT}%")
        print(f"Supported Signals: {', '.join(cls.SUPPORTED_SIGNALS)}")
        print(f"Technical Confirmation: {cls.USE_TECHNICAL_CONFIRMATION}")
        if cls.USE_TECHNICAL_CONFIRMATION:
            print(f"Required Indicators: {', '.join(cls.REQUIRED_INDICATORS)}")
        print(f"Market Filter: {cls.MARKET_FILTER}")
        if cls.MARKET_FILTER:
            print(f"Min Volume 24h: {cls.MIN_VOLUME_24H}")
            print(f"Max Spread: {cls.MAX_SPREAD_PERCENT}%")
        print("=====================================") 