"""Scalping strategy using multiple technical indicators."""

from dataclasses import dataclass, field

import pandas as pd
import ta

from bot.config import SCALPING_CONFIG


@dataclass
class Signal:
    """Represents a trading signal."""

    ticker: str
    action: str  # "BUY" or "SELL"
    price: float
    confidence: float  # 0.0 to 1.0
    indicators: dict = field(default_factory=dict)
    stop_loss: float = 0.0
    take_profit: float = 0.0

    @property
    def confidence_pct(self) -> str:
        return f"{self.confidence * 100:.0f}%"


def compute_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute all technical indicators needed for the scalping strategy.

    Args:
        df: DataFrame with OHLCV columns.

    Returns:
        DataFrame with added indicator columns.
    """
    if df.empty or len(df) < SCALPING_CONFIG["sma_period"]:
        return df

    close = df["Close"]
    high = df["High"]
    low = df["Low"]
    volume = df["Volume"]

    # RSI
    df["rsi"] = ta.momentum.rsi(close, window=SCALPING_CONFIG["rsi_period"])

    # MACD
    macd_indicator = ta.trend.MACD(
        close,
        window_slow=SCALPING_CONFIG["macd_slow"],
        window_fast=SCALPING_CONFIG["macd_fast"],
        window_sign=SCALPING_CONFIG["macd_signal"],
    )
    df["macd"] = macd_indicator.macd()
    df["macd_signal"] = macd_indicator.macd_signal()
    df["macd_histogram"] = macd_indicator.macd_diff()

    # Bollinger Bands
    bb_indicator = ta.volatility.BollingerBands(
        close,
        window=SCALPING_CONFIG["bb_period"],
        window_dev=SCALPING_CONFIG["bb_std_dev"],
    )
    df["bb_upper"] = bb_indicator.bollinger_hband()
    df["bb_middle"] = bb_indicator.bollinger_mavg()
    df["bb_lower"] = bb_indicator.bollinger_lband()

    # EMA (fast and slow)
    df["ema_fast"] = ta.trend.ema_indicator(
        close, window=SCALPING_CONFIG["ema_fast"]
    )
    df["ema_slow"] = ta.trend.ema_indicator(
        close, window=SCALPING_CONFIG["ema_slow"]
    )

    # SMA
    df["sma"] = ta.trend.sma_indicator(close, window=SCALPING_CONFIG["sma_period"])

    # Volume SMA for comparison
    df["volume_sma"] = ta.trend.sma_indicator(
        volume, window=SCALPING_CONFIG["bb_period"]
    )

    # ATR for stop-loss / take-profit calculation
    df["atr"] = ta.volatility.average_true_range(
        high, low, close, window=14
    )

    return df


def _check_rsi(row: pd.Series) -> tuple[int, int, str]:
    """Check RSI signal. Returns (buy_score, sell_score, description)."""
    rsi = row.get("rsi")
    if pd.isna(rsi):
        return 0, 0, "RSI: N/A"

    if rsi <= SCALPING_CONFIG["rsi_oversold"]:
        return 1, 0, f"RSI: {rsi:.1f} (sobreventa)"
    elif rsi >= SCALPING_CONFIG["rsi_overbought"]:
        return 0, 1, f"RSI: {rsi:.1f} (sobrecompra)"
    return 0, 0, f"RSI: {rsi:.1f} (neutral)"


def _check_macd(row: pd.Series) -> tuple[int, int, str]:
    """Check MACD signal."""
    macd = row.get("macd")
    macd_signal = row.get("macd_signal")
    histogram = row.get("macd_histogram")

    if pd.isna(macd) or pd.isna(macd_signal):
        return 0, 0, "MACD: N/A"

    if macd > macd_signal and histogram > 0:
        return 1, 0, f"MACD: cruce alcista (hist={histogram:.4f})"
    elif macd < macd_signal and histogram < 0:
        return 0, 1, f"MACD: cruce bajista (hist={histogram:.4f})"
    return 0, 0, f"MACD: neutral (hist={histogram:.4f})"


def _check_bollinger(row: pd.Series) -> tuple[int, int, str]:
    """Check Bollinger Bands signal."""
    close = row.get("Close")
    bb_lower = row.get("bb_lower")
    bb_upper = row.get("bb_upper")

    if pd.isna(close) or pd.isna(bb_lower) or pd.isna(bb_upper):
        return 0, 0, "BB: N/A"

    if close <= bb_lower:
        return 1, 0, f"BB: precio en banda inferior ({close:.2f} <= {bb_lower:.2f})"
    elif close >= bb_upper:
        return 0, 1, f"BB: precio en banda superior ({close:.2f} >= {bb_upper:.2f})"
    return 0, 0, f"BB: precio dentro de bandas ({close:.2f})"


def _check_ema_cross(row: pd.Series) -> tuple[int, int, str]:
    """Check EMA crossover signal."""
    ema_fast = row.get("ema_fast")
    ema_slow = row.get("ema_slow")

    if pd.isna(ema_fast) or pd.isna(ema_slow):
        return 0, 0, "EMA: N/A"

    diff_pct = ((ema_fast - ema_slow) / ema_slow) * 100
    if ema_fast > ema_slow:
        return 1, 0, f"EMA: cruce alcista (diff={diff_pct:.2f}%)"
    elif ema_fast < ema_slow:
        return 0, 1, f"EMA: cruce bajista (diff={diff_pct:.2f}%)"
    return 0, 0, "EMA: neutral"


def _check_volume(row: pd.Series) -> tuple[int, int, str]:
    """Check if volume is above average (confirms trend)."""
    volume = row.get("Volume")
    volume_sma = row.get("volume_sma")

    if pd.isna(volume) or pd.isna(volume_sma) or volume_sma == 0:
        return 0, 0, "Volumen: N/A"

    ratio = volume / volume_sma
    if ratio >= SCALPING_CONFIG["volume_multiplier"]:
        return 1, 1, f"Volumen: alto ({ratio:.1f}x promedio)"
    return 0, 0, f"Volumen: normal ({ratio:.1f}x promedio)"


def analyze_ticker(ticker: str, df: pd.DataFrame) -> Signal | None:
    """
    Analyze a single ticker using the scalping strategy.

    Evaluates 5 indicators: RSI, MACD, Bollinger Bands, EMA cross, Volume.
    Generates a BUY or SELL signal if enough indicators agree.

    Args:
        ticker: The ticker symbol.
        df: DataFrame with OHLCV data.

    Returns:
        A Signal object if conditions are met, or None.
    """
    if df.empty:
        return None

    df = compute_indicators(df.copy())

    if df.empty or df.iloc[-1].isna().all():
        return None

    last = df.iloc[-1]
    close = last.get("Close")
    atr = last.get("atr")

    if pd.isna(close):
        return None

    # Evaluate all indicators
    checks = [
        _check_rsi(last),
        _check_macd(last),
        _check_bollinger(last),
        _check_ema_cross(last),
        _check_volume(last),
    ]

    buy_total = sum(c[0] for c in checks)
    sell_total = sum(c[1] for c in checks)
    descriptions = {
        f"indicator_{i}": c[2] for i, c in enumerate(checks)
    }

    min_buy = SCALPING_CONFIG["min_signals_buy"]
    min_sell = SCALPING_CONFIG["min_signals_sell"]

    # Calculate stop-loss and take-profit using ATR
    atr_val = float(atr) if not pd.isna(atr) else float(close) * 0.02

    if buy_total >= min_buy and buy_total > sell_total:
        return Signal(
            ticker=ticker,
            action="COMPRA",
            price=float(close),
            confidence=buy_total / 5.0,
            indicators=descriptions,
            stop_loss=float(close) - (atr_val * 1.5),
            take_profit=float(close) + (atr_val * 2.0),
        )
    elif sell_total >= min_sell and sell_total > buy_total:
        return Signal(
            ticker=ticker,
            action="VENTA",
            price=float(close),
            confidence=sell_total / 5.0,
            indicators=descriptions,
            stop_loss=float(close) + (atr_val * 1.5),
            take_profit=float(close) - (atr_val * 2.0),
        )

    return None
