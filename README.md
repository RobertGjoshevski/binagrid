# 🤖 Multi-Strategy Trading Bot

A comprehensive Python-based automated trading bot for Binance that implements multiple trading strategies including Grid Trading, Dollar Cost Averaging (DCA), and Signal-based trading.

## 🚀 Features

### 📊 Grid Trading Bot
- **Grid Strategy**: Automatically places buy/sell orders at predetermined price levels
- **Auto Rebalancing**: Periodically rebalances grid based on market movement
- **Dynamic Grid**: Adjusts grid levels based on market volatility
- **Profit Taking**: Automatic profit taking at configured levels

### 💰 DCA (Dollar Cost Averaging) Bot
- **Scheduled DCA**: Automatic purchases at regular intervals (daily/weekly/monthly)
- **Dip Buying**: Increases purchase amounts during price dips
- **Technical Analysis**: Uses RSI and Moving Averages for entry timing
- **Risk Management**: Daily and total investment limits

### 📡 Signal Trading Bot
- **Multi-Source Signals**: Supports Telegram channels and external APIs
- **Signal Confirmation**: Requires multiple sources to confirm signals
- **Technical Validation**: Uses technical indicators to validate signals
- **Position Management**: Automatic stop-loss and take-profit orders

### 🔧 Common Features
- **Paper Trading Mode**: Test without real money
- **Risk Management**: Configurable stop-loss and take-profit levels
- **Real-time Monitoring**: Live status updates and performance tracking
- **Error Handling**: Robust error handling with automatic retries
- **Rate Limiting**: Built-in API rate limiting to prevent abuse
- **Graceful Shutdown**: Safe shutdown procedures

## 📁 Project Structure

```
Binagrid/
├── main.py                           # Main launcher script
├── .cursorrules                      # Project rules and guidelines
├── README.md                         # This file
├── common/                           # Shared components
│   ├── config.py                     # Common configuration
│   ├── utils.py                      # Shared utilities
│   ├── requirements.txt              # Python dependencies
│   └── env_example.txt               # Environment template
└── strategies/                       # Trading strategies
    ├── grid_bot/                     # Grid Trading Bot
    │   ├── grid_bot.py               # Grid bot implementation
    │   └── grid_config.py            # Grid-specific configuration
    ├── dca_bot/                      # DCA Trading Bot
    │   ├── dca_bot.py                # DCA bot implementation
    │   └── dca_config.py             # DCA-specific configuration
    └── signal_bot/                   # Signal Trading Bot
        ├── signal_bot.py             # Signal bot implementation
        └── signal_config.py          # Signal-specific configuration
```

## 🛠️ Installation

### Prerequisites
- Python 3.7 or higher
- Binance account with API access
- Basic understanding of cryptocurrency trading

### Setup Steps

1. **Clone or download the project files**

2. **Install Python dependencies**:
   ```bash
   cd common
   pip install -r requirements.txt
   ```

3. **Set up your environment variables**:
   ```bash
   cd common
   cp env_example.txt .env
   
   # Edit .env with your actual API keys and settings
   nano .env
   ```

## ⚙️ Configuration

### API Keys Setup

1. Go to [Binance API Management](https://www.binance.com/en/my/settings/api-management)
2. Create a new API key
3. Enable spot trading permissions
4. Copy your API key and secret to the `common/.env` file

### Strategy-Specific Configuration

Each strategy has its own configuration section in the `.env` file:

#### Grid Trading Bot
```env
# Grid Strategy Parameters
GRID_LEVELS=10
GRID_SPACING_PERCENT=1.0
GRID_TYPE=ARITHMETIC
AUTO_REBALANCE=True
```

#### DCA Bot
```env
# DCA Strategy Parameters
DCA_INTERVAL=DAILY
DCA_AMOUNT=50.0
DCA_TIME=09:00
DCA_ON_DIP=True
DIP_THRESHOLD=5.0
```

#### Signal Bot
```env
# Signal Sources
SIGNAL_SOURCES=TELEGRAM,API
SIGNAL_CONFIRMATION=2
POSITION_SIZE_PERCENT=10.0
```

## 🚀 Usage

### Interactive Mode
```bash
python3 main.py
```
This will show a menu to select which strategy to run.

### Command Line Mode
```bash
# Run Grid Trading Bot
python3 main.py --strategy grid

# Run DCA Bot
python3 main.py --strategy dca

# Run Signal Bot
python3 main.py --strategy signal

# Validate environment
python3 main.py --validate
```

### Direct Strategy Execution
```bash
# Grid Bot
python3 strategies/grid_bot/grid_bot.py

# DCA Bot
python3 strategies/dca_bot/dca_bot.py

# Signal Bot
python3 strategies/signal_bot/signal_bot.py
```

## 📊 Strategy Details

### Grid Trading Strategy

**How It Works:**
1. Creates a grid of price levels around current market price
2. Places buy orders below current price
3. Places sell orders above current price
4. When a buy order fills, places sell order at next higher level
5. Profits from price differences between grid levels

**Example:**
- BTCUSDT at $50,000 with 1% spacing
- Buy orders at: $49,500, $49,000, $48,500
- Sell orders at: $50,500, $51,000, $51,500
- Profit potential: $1,000 per BTC traded

### DCA Strategy

**How It Works:**
1. Buys fixed amount at regular intervals (daily/weekly/monthly)
2. Increases purchase amount during price dips
3. Uses technical indicators for optimal entry timing
4. Averages down during market corrections

**Features:**
- Scheduled purchases
- Dip detection and enhanced buying
- Technical analysis integration
- Investment limits and risk management

### Signal Trading Strategy

**How It Works:**
1. Monitors multiple signal sources (Telegram, APIs)
2. Requires signal confirmation from multiple sources
3. Validates signals with technical analysis
4. Executes trades with position sizing and risk management

**Features:**
- Multi-source signal aggregation
- Technical validation
- Position management
- Performance tracking

## 🛡️ Risk Management

### Built-in Safety Features

- **Paper Trading Mode**: Test without real money
- **Stop Loss**: Automatic stop-loss at configured percentage
- **Daily Loss Limit**: Maximum daily loss protection
- **Order Validation**: Validates all orders before placement
- **Error Handling**: Automatic retries on API errors
- **Position Limits**: Maximum concurrent positions
- **Investment Limits**: Total investment caps

### Risk Warnings

⚠️ **IMPORTANT**: Cryptocurrency trading involves significant risk. This bot is for educational purposes. Always:

- Start with paper trading
- Use only funds you can afford to lose
- Monitor the bot regularly
- Understand each strategy before using
- Test thoroughly before live trading

## 🔧 Troubleshooting

### Common Issues

1. **API Key Errors**:
   - Ensure API keys are correct
   - Check API permissions (spot trading enabled)
   - Verify testnet vs mainnet settings

2. **Order Placement Failures**:
   - Check account balance
   - Verify trading pair is active
   - Check minimum order requirements

3. **Import Errors**:
   - Ensure all dependencies are installed
   - Check Python path configuration
   - Verify file structure

### Environment Validation

Run the validation command to check your setup:
```bash
python3 main.py --validate
```

## 📈 Performance Monitoring

Each bot provides real-time statistics including:
- Current market price
- Total trades executed
- Trading volume
- Unrealized PnL
- Uptime
- Strategy-specific metrics

## 🔄 Adding New Strategies

To add a new trading strategy:

1. Create a new folder in `strategies/`
2. Create `strategy_config.py` with strategy-specific settings
3. Create `strategy_bot.py` with the bot implementation
4. Update `main.py` to include the new strategy
5. Add configuration options to `env_example.txt`

## 🤝 Contributing

Feel free to contribute improvements:
- Bug fixes
- New strategies
- Documentation updates
- Performance optimizations
- Additional features

## 📄 License

This project is for educational purposes. Please ensure compliance with your local regulations regarding automated trading.

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section
2. Review the logs for error messages
3. Ensure proper configuration
4. Test with paper trading first

---

**Remember**: Always start with paper trading and small amounts when testing any trading bot! 