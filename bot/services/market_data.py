"""Market data fetching module using yfinance."""

import yfinance as yf
import pandas as pd
from datetime import datetime


def fetch_market_data(
    ticker: str, period: str = "5d", interval: str = "15m"
) -> pd.DataFrame:
    """
    Fetch historical market data for a given ticker.

    Args:
        ticker: Stock/crypto ticker symbol (e.g., 'AAPL', 'BTC-USD').
        period: Data period to download (e.g., '1d', '5d', '1mo').
        interval: Data interval (e.g., '1m', '5m', '15m', '1h', '1d').

    Returns:
        DataFrame with OHLCV data, or empty DataFrame on error.
    """
    try:
        data = yf.download(
            ticker,
            period=period,
            interval=interval,
            progress=False,
            auto_adjust=True,
        )
        if data.empty:
            print(f"[{datetime.now()}] No data returned for {ticker}")
            return pd.DataFrame()

        # Flatten MultiIndex columns if present
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)

        return data
    except Exception as e:
        print(f"[{datetime.now()}] Error fetching data for {ticker}: {e}")
        return pd.DataFrame()


def get_current_price(ticker: str) -> float | None:
    """
    Get the most recent price for a ticker.

    Args:
        ticker: Stock/crypto ticker symbol.

    Returns:
        Current price as float, or None on error.
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.fast_info
        return float(info.last_price)
    except Exception as e:
        print(f"[{datetime.now()}] Error getting price for {ticker}: {e}")
        return None
