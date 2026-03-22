"""Configuration module for the Scalping Trading Bot."""

import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# Market Configuration
TICKERS_STR = os.getenv("TICKERS", "AAPL,MSFT,GOOGL,AMZN,TSLA,META,NVDA,BTC-USD,ETH-USD")
TICKERS = [t.strip() for t in TICKERS_STR.split(",") if t.strip()]

# Analysis interval in hours
ANALYSIS_INTERVAL = int(os.getenv("ANALYSIS_INTERVAL", "1"))

# Timezone
TIMEZONE = os.getenv("TIMEZONE", "America/Mexico_City")

# Scalping Strategy Parameters
SCALPING_CONFIG = {
    # RSI
    "rsi_period": 14,
    "rsi_overbought": 70,
    "rsi_oversold": 30,

    # MACD
    "macd_fast": 12,
    "macd_slow": 26,
    "macd_signal": 9,

    # Bollinger Bands
    "bb_period": 20,
    "bb_std_dev": 2,

    # Moving Averages
    "ema_fast": 9,
    "ema_slow": 21,
    "sma_period": 50,

    # Volume
    "volume_multiplier": 1.5,

    # Minimum signals required to generate an alert (out of 5 indicators)
    "min_signals_buy": 3,
    "min_signals_sell": 3,

    # Data period for analysis
    "data_period": "5d",
    "data_interval": "15m",
}
