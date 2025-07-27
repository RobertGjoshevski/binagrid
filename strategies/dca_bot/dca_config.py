"""
DCA (Dollar Cost Averaging) Bot Configuration
Specific settings for DCA trading strategy.
"""

import os
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv('../common/.env')

class DCAConfig:
    """Configuration class for the DCA Trading Bot."""
    
    # Bot Identity
    BOT_NAME = "DCA Trading Bot"
    BOT_TYPE = "DCA"
    
    # DCA Strategy Parameters
    DCA_INTERVAL = os.getenv('DCA_INTERVAL', 'DAILY')  # DAILY, WEEKLY, MONTHLY
    DCA_AMOUNT = float(os.getenv('DCA_AMOUNT', '50.0'))  # USDT per interval
    DCA_TIME = os.getenv('DCA_TIME', '09:00')  # Time to execute DCA (24h format)
    
    # DCA Behavior
    DCA_ON_DIP = os.getenv('DCA_ON_DIP', 'True').lower() == 'true'
    DIP_THRESHOLD = float(os.getenv('DIP_THRESHOLD', '5.0'))  # % drop to trigger extra DCA
    EXTRA_DCA_MULTIPLIER = float(os.getenv('EXTRA_DCA_MULTIPLIER', '1.5'))  # Multiply amount on dips
    
    # Market Analysis
    USE_TECHNICAL_INDICATORS = os.getenv('USE_TECHNICAL_INDICATORS', 'True').lower() == 'true'
    RSI_OVERSOLD = int(os.getenv('RSI_OVERSOLD', '30'))
    RSI_OVERBOUGHT = int(os.getenv('RSI_OVERBOUGHT', '70'))
    MA_PERIOD = int(os.getenv('MA_PERIOD', '20'))
    
    # Risk Management
    MAX_DCA_PER_DAY = int(os.getenv('MAX_DCA_PER_DAY', '3'))
    MAX_TOTAL_INVESTMENT = float(os.getenv('MAX_TOTAL_INVESTMENT', '10000.0'))
    STOP_LOSS_PERCENT = float(os.getenv('STOP_LOSS_PERCENT', '20.0'))
    
    # DCA Scheduling
    ENABLE_SCHEDULING = os.getenv('ENABLE_SCHEDULING', 'True').lower() == 'true'
    TIMEZONE = os.getenv('TIMEZONE', 'UTC')
    
    # Advanced DCA
    VOLATILITY_ADJUSTMENT = os.getenv('VOLATILITY_ADJUSTMENT', 'True').lower() == 'true'
    VOLATILITY_THRESHOLD = float(os.getenv('VOLATILITY_THRESHOLD', '10.0'))
    
    @classmethod
    def validate_config(cls) -> bool:
        """Validate DCA-specific configuration."""
        if cls.DCA_AMOUNT <= 0:
            print("ERROR: DCA_AMOUNT must be greater than 0")
            return False
        
        if cls.DCA_INTERVAL not in ['DAILY', 'WEEKLY', 'MONTHLY']:
            print("ERROR: DCA_INTERVAL must be DAILY, WEEKLY, or MONTHLY")
            return False
        
        if cls.DIP_THRESHOLD <= 0 or cls.DIP_THRESHOLD > 50:
            print("ERROR: DIP_THRESHOLD must be between 0 and 50")
            return False
        
        if cls.MAX_DCA_PER_DAY <= 0:
            print("ERROR: MAX_DCA_PER_DAY must be greater than 0")
            return False
        
        return True
    
    @classmethod
    def print_config(cls) -> None:
        """Print DCA-specific configuration."""
        print("=== DCA Trading Bot Configuration ===")
        print(f"DCA Interval: {cls.DCA_INTERVAL}")
        print(f"DCA Amount: {cls.DCA_AMOUNT} USDT")
        print(f"DCA Time: {cls.DCA_TIME}")
        print(f"DCA on Dip: {cls.DCA_ON_DIP}")
        if cls.DCA_ON_DIP:
            print(f"Dip Threshold: {cls.DIP_THRESHOLD}%")
            print(f"Extra DCA Multiplier: {cls.EXTRA_DCA_MULTIPLIER}x")
        print(f"Max DCA per Day: {cls.MAX_DCA_PER_DAY}")
        print(f"Max Total Investment: {cls.MAX_TOTAL_INVESTMENT} USDT")
        print(f"Stop Loss: {cls.STOP_LOSS_PERCENT}%")
        print(f"Technical Indicators: {cls.USE_TECHNICAL_INDICATORS}")
        if cls.USE_TECHNICAL_INDICATORS:
            print(f"RSI Oversold: {cls.RSI_OVERSOLD}")
            print(f"RSI Overbought: {cls.RSI_OVERBOUGHT}")
            print(f"MA Period: {cls.MA_PERIOD}")
        print("=====================================") 