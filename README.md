# ETH Trend Analyzer v2.0

Real-time Ethereum trend analysis system with Fibonacci retracement tracking and swing point detection. The system provides both minute-by-minute Fibonacci analysis and 5-minute swing analysis with automated Telegram reporting.

## 🚀 Features

### Real-time Analysis
- **Fibonacci Retracement Tracking**: Every new 1-minute candle is analyzed against the previous candle for Fibonacci retracement levels
- **Swing Point Detection**: Identifies swing highs and lows using 10+10 lookback/lookforward algorithm
- **Live Price Monitoring**: Real-time ETH/USDT price tracking via Binance WebSocket

### Automated Reporting
- **Telegram Integration**: Automated reports sent to configured Telegram chat
- **Dual Analysis System**: 
  - Real-time Fibonacci reports (every minute)
  - Swing analysis reports (every 5 minutes)
- **Detailed Logging**: Complete system logs saved to file

### Technical Analysis
- **Trend Direction**: BULLISH/BEARISH/SIDEWAYS based on swing breakouts
- **Confidence Scoring**: Algorithm confidence levels for trend predictions
- **Fibonacci Levels**: 0%, 23.6%, 38.2%, 50%, 61.8%, 78.6%, 100%
- **Historical Data**: 1000-candle historical analysis for swing detection

## 📊 System Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Binance API   │───▶│  WebSocket       │───▶│  Fibonacci      │
│   Historical    │    │  Handler         │    │  Analyzer       │
│   + Real-time   │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌──────────────────┐    ┌─────────────────┐
                       │  Telegram Bot    │    │  Swing Point    │
                       │  Notifications   │    │  Detection      │
                       │                  │    │                 │
                       └──────────────────┘    └─────────────────┘
```

## 🔧 Installation

### Prerequisites
- Python 3.8+
- Telegram Bot Token
- Telegram Chat ID

### Dependencies
```bash
pip install -r requirements.txt
```

Required packages:
```
websockets>=11.0.3
aiohttp>=3.8.5
requests>=2.31.0
pandas>=2.0.3
numpy>=1.24.3
```

### Configuration

1. **Environment Variables** (Recommended):
```bash
export TELEGRAM_BOT_TOKEN="your_bot_token_here"
export TELEGRAM_CHAT_ID="your_chat_id_here"
```

2. **PowerShell (Windows)**:
```powershell
$env:TELEGRAM_BOT_TOKEN="your_bot_token_here"
$env:TELEGRAM_CHAT_ID="your_chat_id_here"
```

## 🏃‍♂️ Usage

### Basic Usage
```bash
python main.py
```

### System Output

**Console Output (Real-time Fibonacci)**:
```
🔍 REAL-TIME FIBONACCI ANALYSIS [05:43:59]:
   Previous Candle: High=$4675.41, Low=$4673.25, Range=$2.16
   Current Candle: High=$4677.82, Low=$4676.00, Close=$4677.82
   📐 Fibonacci Level: 0.618 (61.8%)
   📊 Direction: recovery_after_bearish
   🎯 GOLDEN RATIO LEVEL!
```

**Console Output (5-Minute Swing Analysis)**:
```
📊 ETH Analysis Summary
Current Price: $4674.00
Direction: SIDEWAYS (Confidence: 72.7%)
🔺 Last Swing High: $4691.30 (28 mum önce)
🔻 Last Swing Low: $4668.92 (42 mum önce)
Avg Fibonacci Retracement: 49.8%
```

### Telegram Notifications

**Real-time Fibonacci (Every Minute)**:
```
🕯️ Real-time Fibonacci | 05:43:59
🎯 Fibonacci: 0.618 (61.8%) 💪
📈 Recovery

Previous Candle:
High: $4675.41 | Low: $4673.25 | Range: $2.16

Current Candle: 
High: $4677.82 | Low: $4676.00
Close: $4677.82
```

**Swing Analysis (Every 5 Minutes)**:
```
🎯 5-Min Swing Analysis | 05:43:59
Direction: SIDEWAYS ↔️📊
Confidence: 72.7%

🔺 Last Swing High: $4691.30 (28 candles ago)
🔻 Last Swing Low: $4668.92 (42 candles ago)

📊 Range Position: Middle area (47%)
💡 Breakout Levels: Above $4691.30 (Bullish) or Below $4668.92 (Bearish)
```

## 📁 Project Structure

```
eth-trend-analyzer-simple/
├── main.py                    # Main application entry point
├── simple_analyzer.py         # Core analysis algorithms
├── websocket_handler.py       # Binance WebSocket management
├── telegram_bot.py           # Telegram integration
├── requirements.txt          # Python dependencies
├── eth_analyzer.log         # System logs (auto-generated)
└── README.md               # This documentation
```

## 🔬 Technical Details

### Fibonacci Retracement Algorithm
```python
def calculate_fibonacci_retracement(prev_candle, current_candle):
    """
    Calculates Fibonacci retracement level between two consecutive candles
    
    For bullish previous candle: (prev_high - current_low) / prev_range
    For bearish previous candle: (current_high - prev_low) / prev_range
    
    Returns closest Fibonacci level: 0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0
    """
```

### Swing Point Detection
```python
def find_swing_points(candles, lookback=10, lookforward=10):
    """
    Identifies swing highs and lows using lookback/lookforward algorithm
    
    Swing High: Highest point within lookback+lookforward window
    Swing Low: Lowest point within lookback+lookforward window
    
    Default: 10 candles back + 10 candles forward = 21-candle window
    """
```

### Trend Detection Logic
- **BULLISH**: Current high > Last swing high
- **BEARISH**: Current low < Last swing low  
- **SIDEWAYS**: No swing levels broken
- **Confidence**: Based on breakout distance and market conditions

## 📈 Analysis Parameters

| Parameter | Value | Description |
|-----------|-------|-------------|
| Historical Data | 1000 candles | Initial data for swing detection |
| Analysis Window | 20 candles | Fibonacci average calculation |
| Update Interval | 5 minutes | Swing analysis frequency |
| Swing Lookback | 10 candles | Swing detection parameter |
| Swing Lookforward | 10 candles | Swing detection parameter |
| Timeframe | 1 minute | Candle resolution |

## 🔧 Customization

### Modify Analysis Parameters
```python
# In simple_analyzer.py
self.ANALYSIS_WINDOW = 20     # Change Fibonacci window
self.UPDATE_INTERVAL = 5      # Change update frequency

# In websocket_handler.py and simple_analyzer.py
lookback=10, lookforward=10   # Change swing detection sensitivity
```

### Add Custom Fibonacci Levels
```python
# In simple_analyzer.py calculate_fibonacci_retracement()
fib_levels = [0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0, 1.272, 1.618]
```

## 📊 System Requirements

- **Memory**: ~50MB RAM usage
- **Network**: Stable internet connection for WebSocket
- **CPU**: Minimal usage, event-driven architecture
- **Storage**: ~1MB per day for logs

## 🐛 Troubleshooting

### Common Issues

**WebSocket Connection Failed**:
```bash
# Check internet connection and try restarting
python main.py
```

**Telegram Messages Not Sending**:
- Verify `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID`
- Check bot has permission to send messages to the chat

**"Insufficient Data" Messages**:
- Wait for system to load 1000+ historical candles
- Check Binance API connectivity

### Logs
System logs are automatically saved to `eth_analyzer.log`:
```bash
tail -f eth_analyzer.log  # Follow logs in real-time
```

## 📋 Changelog

### v2.0 (Current)
- ✅ Real-time Fibonacci retracement tracking
- ✅ Swing-based trend analysis
- ✅ Dual Telegram reporting system
- ✅ Enhanced logging and error handling
- ✅ Modular architecture

### v1.0 (Legacy)
- Basic Fibonacci calculations
- Simple trend detection
- Single Telegram reports

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## ⚠️ Disclaimer

This tool is for educational and research purposes only. It is not financial advice. Cryptocurrency trading involves significant risk and you should never trade with money you cannot afford to lose.

## 📞 Support

For issues, questions, or feature requests:
- Create an issue in the GitHub repository
- Review the troubleshooting section
- Check system logs for error details

---

**ETH Trend Analyzer v2.0** - Real-time Fibonacci tracking meets swing analysis for comprehensive ETH trend monitoring.
