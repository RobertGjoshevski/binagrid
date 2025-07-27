"""
Grid Trading Bot Configuration
Specific settings for grid trading strategy.
"""

import os
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv('../common/.env')

class GridConfig:
    """Configuration class for the Grid Trading Bot."""
    
    # Bot Identity
    BOT_NAME = "Grid Trading Bot"
    BOT_TYPE = "GRID"
    
    # Grid Strategy Parameters
    GRID_LEVELS = int(os.getenv('GRID_LEVELS', '10'))
    GRID_SPACING_PERCENT = float(os.getenv('GRID_SPACING_PERCENT', '1.0'))
    GRID_TYPE = os.getenv('GRID_TYPE', 'ARITHMETIC')  # ARITHMETIC or GEOMETRIC
    
    # Order Management
    BASE_ORDER_SIZE = float(os.getenv('BASE_ORDER_SIZE', '10.0'))  # USDT per grid level
    REBALANCE_INTERVAL = int(os.getenv('REBALANCE_INTERVAL', '300'))  # seconds
    
    # Grid Behavior
    AUTO_REBALANCE = os.getenv('AUTO_REBALANCE', 'True').lower() == 'true'
    DYNAMIC_GRID = os.getenv('DYNAMIC_GRID', 'False').lower() == 'true'
    GRID_EXPANSION = os.getenv('GRID_EXPANSION', 'False').lower() == 'true'
    
    # Risk Management
    MAX_GRID_LEVELS = int(os.getenv('MAX_GRID_LEVELS', '20'))
    MIN_GRID_SPACING = float(os.getenv('MIN_GRID_SPACING', '0.5'))
    MAX_GRID_SPACING = float(os.getenv('MAX_GRID_SPACING', '5.0'))
    
    # Grid Performance
    PROFIT_TAKING_ENABLED = os.getenv('PROFIT_TAKING_ENABLED', 'True').lower() == 'true'
    PROFIT_TAKING_PERCENT = float(os.getenv('PROFIT_TAKING_PERCENT', '2.0'))
    
    @classmethod
    def validate_config(cls) -> bool:
        """Validate grid-specific configuration."""
        if cls.GRID_LEVELS <= 0 or cls.GRID_LEVELS > cls.MAX_GRID_LEVELS:
            print(f"ERROR: GRID_LEVELS must be between 1 and {cls.MAX_GRID_LEVELS}")
            return False
        
        if cls.GRID_SPACING_PERCENT < cls.MIN_GRID_SPACING or cls.GRID_SPACING_PERCENT > cls.MAX_GRID_SPACING:
            print(f"ERROR: GRID_SPACING_PERCENT must be between {cls.MIN_GRID_SPACING} and {cls.MAX_GRID_SPACING}")
            return False
        
        if cls.BASE_ORDER_SIZE <= 0:
            print("ERROR: BASE_ORDER_SIZE must be greater than 0")
            return False
        
        return True
    
    @classmethod
    def print_config(cls) -> None:
        """Print grid-specific configuration."""
        print("=== Grid Trading Bot Configuration ===")
        print(f"Grid Levels: {cls.GRID_LEVELS}")
        print(f"Grid Spacing: {cls.GRID_SPACING_PERCENT}%")
        print(f"Grid Type: {cls.GRID_TYPE}")
        print(f"Base Order Size: {cls.BASE_ORDER_SIZE} USDT")
        print(f"Auto Rebalance: {cls.AUTO_REBALANCE}")
        print(f"Dynamic Grid: {cls.DYNAMIC_GRID}")
        print(f"Grid Expansion: {cls.GRID_EXPANSION}")
        print(f"Profit Taking: {cls.PROFIT_TAKING_ENABLED}")
        if cls.PROFIT_TAKING_ENABLED:
            print(f"Profit Taking %: {cls.PROFIT_TAKING_PERCENT}%")
        print("=====================================") 