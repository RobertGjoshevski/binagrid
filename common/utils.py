"""
Utility functions for the Binance Grid Trading Bot.
Includes price calculations, order formatting, and helper functions.
"""

import math
import time
import logging
from typing import List, Tuple, Dict, Any, Optional
from datetime import datetime, timedelta
from binance.exceptions import BinanceAPIException
from config import get_trading_pair_config

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def calculate_grid_levels(
    current_price: float,
    grid_levels: int,
    grid_spacing_percent: float,
    grid_type: str = 'ARITHMETIC'
) -> List[float]:
    """
    Calculate grid price levels based on current price and parameters.
    
    Args:
        current_price: Current market price
        grid_levels: Number of grid levels
        grid_spacing_percent: Percentage spacing between levels
        grid_type: 'ARITHMETIC' or 'GEOMETRIC'
    
    Returns:
        List of price levels for the grid
    """
    levels = []
    spacing = grid_spacing_percent / 100.0
    
    if grid_type.upper() == 'ARITHMETIC':
        # Arithmetic grid: equal price differences
        price_step = current_price * spacing
        half_levels = grid_levels // 2
        
        for i in range(-half_levels, half_levels + 1):
            level_price = current_price + (i * price_step)
            if level_price > 0:
                levels.append(level_price)
    
    elif grid_type.upper() == 'GEOMETRIC':
        # Geometric grid: equal percentage differences
        multiplier = 1 + spacing
        half_levels = grid_levels // 2
        
        for i in range(-half_levels, half_levels + 1):
            level_price = current_price * (multiplier ** i)
            if level_price > 0:
                levels.append(level_price)
    
    return sorted(levels)

def format_quantity(quantity: float, symbol: str) -> float:
    """
    Format quantity according to trading pair precision requirements.
    
    Args:
        quantity: Raw quantity
        symbol: Trading pair symbol (e.g., 'BTCUSDT')
    
    Returns:
        Formatted quantity
    """
    config = get_trading_pair_config(symbol)
    precision = config['quantity_precision']
    step_size = config['step_size']
    
    # Round to step size
    quantity = round(quantity / step_size) * step_size
    
    # Round to precision
    return round(quantity, precision)

def format_price(price: float, symbol: str) -> float:
    """
    Format price according to trading pair precision requirements.
    
    Args:
        price: Raw price
        symbol: Trading pair symbol (e.g., 'BTCUSDT')
    
    Returns:
        Formatted price
    """
    config = get_trading_pair_config(symbol)
    precision = config['price_precision']
    
    return round(price, precision)

def calculate_order_size(base_size: float, price: float, symbol: str) -> float:
    """
    Calculate order size in base currency based on USDT value.
    
    Args:
        base_size: Base order size in USDT
        price: Current price
        symbol: Trading pair symbol
    
    Returns:
        Order size in base currency
    """
    quantity = base_size / price
    return format_quantity(quantity, symbol)

def validate_order_parameters(
    symbol: str,
    quantity: float,
    price: float
) -> Tuple[bool, str]:
    """
    Validate order parameters against trading pair requirements.
    
    Args:
        symbol: Trading pair symbol
        quantity: Order quantity
        price: Order price
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    config = get_trading_pair_config(symbol)
    
    # Check minimum quantity
    if quantity < config['min_qty']:
        return False, f"Quantity {quantity} is below minimum {config['min_qty']}"
    
    # Check step size
    if quantity % config['step_size'] != 0:
        return False, f"Quantity {quantity} is not a multiple of step size {config['step_size']}"
    
    # Check price precision
    formatted_price = format_price(price, symbol)
    if abs(price - formatted_price) > 0.000001:
        return False, f"Price {price} does not match precision requirements"
    
    return True, ""

def calculate_pnl(
    entry_price: float,
    current_price: float,
    quantity: float,
    side: str
) -> float:
    """
    Calculate profit/loss for a position.
    
    Args:
        entry_price: Entry price
        current_price: Current market price
        quantity: Position quantity
        side: 'BUY' or 'SELL'
    
    Returns:
        Profit/loss in USDT
    """
    if side.upper() == 'BUY':
        return (current_price - entry_price) * quantity
    else:  # SELL
        return (entry_price - current_price) * quantity

def calculate_total_pnl(positions: List[Dict[str, Any]]) -> float:
    """
    Calculate total PnL across all positions.
    
    Args:
        positions: List of position dictionaries
    
    Returns:
        Total PnL in USDT
    """
    total_pnl = 0.0
    for position in positions:
        pnl = calculate_pnl(
            position['entry_price'],
            position['current_price'],
            position['quantity'],
            position['side']
        )
        total_pnl += pnl
    
    return total_pnl

def get_current_timestamp() -> int:
    """Get current timestamp in milliseconds."""
    return int(time.time() * 1000)

def format_timestamp(timestamp: int) -> str:
    """Format timestamp to readable string."""
    return datetime.fromtimestamp(timestamp / 1000).strftime('%Y-%m-%d %H:%M:%S')

def retry_on_error(
    func,
    max_retries: int = 3,
    delay: float = 1.0,
    backoff_factor: float = 2.0
):
    """
    Decorator to retry function calls on API errors.
    
    Args:
        func: Function to retry
        max_retries: Maximum number of retries
        delay: Initial delay between retries
        backoff_factor: Multiplier for delay on each retry
    """
    def wrapper(*args, **kwargs):
        last_exception = None
        current_delay = delay
        
        for attempt in range(max_retries + 1):
            try:
                return func(*args, **kwargs)
            except BinanceAPIException as e:
                last_exception = e
                if e.code in [429, 418]:  # Rate limit errors
                    logger.warning(f"Rate limit hit, waiting {current_delay}s (attempt {attempt + 1})")
                    time.sleep(current_delay)
                    current_delay *= backoff_factor
                elif e.code in [502, 503, 504]:  # Server errors
                    logger.warning(f"Server error, retrying in {current_delay}s (attempt {attempt + 1})")
                    time.sleep(current_delay)
                    current_delay *= backoff_factor
                else:
                    raise e
            except Exception as e:
                last_exception = e
                if attempt < max_retries:
                    logger.warning(f"Error occurred, retrying in {current_delay}s (attempt {attempt + 1}): {e}")
                    time.sleep(current_delay)
                    current_delay *= backoff_factor
                else:
                    raise e
        
        if last_exception:
            raise last_exception
    
    return wrapper

def calculate_grid_performance(
    grid_levels: List[float],
    executed_orders: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Calculate grid trading performance metrics.
    
    Args:
        grid_levels: List of grid price levels
        executed_orders: List of executed orders
    
    Returns:
        Dictionary with performance metrics
    """
    if not executed_orders:
        return {
            'total_trades': 0,
            'total_volume': 0,
            'total_fees': 0,
            'net_pnl': 0,
            'win_rate': 0,
            'avg_trade_size': 0
        }
    
    total_trades = len(executed_orders)
    total_volume = sum(order['quantity'] * order['price'] for order in executed_orders)
    total_fees = sum(order.get('commission', 0) for order in executed_orders)
    
    # Calculate PnL (simplified - assumes we're tracking positions properly)
    net_pnl = 0  # This would need to be calculated based on actual position tracking
    
    # Calculate win rate (simplified)
    profitable_trades = sum(1 for order in executed_orders if order.get('realized_pnl', 0) > 0)
    win_rate = (profitable_trades / total_trades) * 100 if total_trades > 0 else 0
    
    avg_trade_size = total_volume / total_trades if total_trades > 0 else 0
    
    return {
        'total_trades': total_trades,
        'total_volume': total_volume,
        'total_fees': total_fees,
        'net_pnl': net_pnl,
        'win_rate': win_rate,
        'avg_trade_size': avg_trade_size
    }

def log_trade_execution(order: Dict[str, Any], grid_level: float) -> None:
    """
    Log trade execution details.
    
    Args:
        order: Order details
        grid_level: Grid level where order was executed
    """
    logger.info(
        f"Trade executed: {order['side']} {order['quantity']} {order['symbol']} "
        f"@ {order['price']} (Grid Level: {grid_level})"
    )

def is_market_open() -> bool:
    """
    Check if the market is currently open.
    Note: Crypto markets are 24/7, but this function can be extended
    for specific market hours if needed.
    
    Returns:
        True if market is open
    """
    # Crypto markets are always open
    return True

def calculate_optimal_grid_spacing(
    volatility: float,
    base_spacing: float = 1.0
) -> float:
    """
    Calculate optimal grid spacing based on market volatility.
    
    Args:
        volatility: Market volatility (standard deviation)
        base_spacing: Base spacing percentage
    
    Returns:
        Optimal grid spacing percentage
    """
    # Simple volatility adjustment
    # Higher volatility = wider spacing
    volatility_multiplier = 1 + (volatility * 0.1)
    return base_spacing * volatility_multiplier 