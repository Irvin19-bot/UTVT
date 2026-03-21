"""
Scalping Trading Bot - Entry Point

A trading bot that uses scalping strategies with technical indicators
(RSI, MACD, Bollinger Bands, EMA/SMA) to analyze markets and send
operation alerts to a Telegram group.

Usage:
    python main.py              # Run with scheduler (continuous)
    python main.py --once       # Run analysis once and exit
"""

import sys
import time
from datetime import datetime

import schedule

from bot.analyzer import run_analysis
from bot.config import ANALYSIS_INTERVAL, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, TIMEZONE
from bot.services.telegram_service import send_startup_message


def scheduled_analysis() -> None:
    """Wrapper for scheduled analysis execution."""
    try:
        run_analysis()
    except Exception as e:
        print(f"[{datetime.now()}] Error during analysis: {e}")


def main() -> None:
    """Main entry point for the trading bot."""
    print(r"""
    ╔══════════════════════════════════════════╗
    ║     🤖 SCALPING TRADING BOT v1.0        ║
    ║     Estrategia: Multi-Indicador         ║
    ║     RSI | MACD | BB | EMA | Volumen     ║
    ╚══════════════════════════════════════════╝
    """)

    # Validate configuration
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print(
            "⚠️  ADVERTENCIA: Las credenciales de Telegram no estan configuradas.\n"
            "   Las alertas se mostraran solo en consola.\n"
            "   Configura TELEGRAM_BOT_TOKEN y TELEGRAM_CHAT_ID en el archivo .env\n"
        )
    else:
        print("✅ Credenciales de Telegram configuradas correctamente.\n")
        send_startup_message()

    # Single run mode
    if "--once" in sys.argv:
        print("Modo: ejecucion unica\n")
        run_analysis()
        print("\nAnalisis completado. Saliendo...")
        return

    # Scheduled mode
    print(f"Modo: programado (cada {ANALYSIS_INTERVAL} hora(s))")
    print(f"Zona horaria: {TIMEZONE}\n")

    # Run immediately on start
    run_analysis()

    # Schedule subsequent runs
    schedule.every(ANALYSIS_INTERVAL).hours.do(scheduled_analysis)

    print(f"\n[{datetime.now()}] Programador activo. Esperando siguiente ejecucion...")
    print("Presiona Ctrl+C para detener el bot.\n")

    try:
        while True:
            schedule.run_pending()
            time.sleep(60)
    except KeyboardInterrupt:
        print(f"\n[{datetime.now()}] Bot detenido por el usuario.")


if __name__ == "__main__":
    main()
