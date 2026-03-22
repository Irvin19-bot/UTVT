"""Main market analyzer module that orchestrates the scalping analysis."""

from datetime import datetime

from bot.config import TICKERS, SCALPING_CONFIG
from bot.services.market_data import fetch_market_data
from bot.services.telegram_service import send_signal_alert, send_summary
from bot.strategies.scalping import Signal, analyze_ticker


def run_analysis() -> list[Signal]:
    """
    Run the scalping analysis on all configured tickers.

    Fetches market data for each ticker, applies the scalping strategy,
    and sends alerts for any signals found.

    Returns:
        List of generated trading signals.
    """
    print(f"\n{'=' * 60}")
    print(f"[{datetime.now()}] Iniciando analisis de mercado...")
    print(f"Tickers a analizar: {', '.join(TICKERS)}")
    print(f"{'=' * 60}\n")

    signals: list[Signal] = []
    period = SCALPING_CONFIG["data_period"]
    interval = SCALPING_CONFIG["data_interval"]

    for ticker in TICKERS:
        print(f"[{datetime.now()}] Analizando {ticker}...")

        df = fetch_market_data(ticker, period=period, interval=interval)
        if df.empty:
            print(f"  -> Sin datos para {ticker}, saltando...")
            continue

        signal = analyze_ticker(ticker, df)

        if signal is not None:
            signals.append(signal)
            print(
                f"  -> SENAL {signal.action} detectada para {ticker} "
                f"@ ${signal.price:,.2f} (confianza: {signal.confidence_pct})"
            )
            send_signal_alert(signal)
        else:
            print(f"  -> Sin senal para {ticker}")

    # Send summary
    print(f"\n[{datetime.now()}] Analisis completado.")
    print(f"Senales encontradas: {len(signals)}")

    send_summary(signals, len(TICKERS))

    return signals
