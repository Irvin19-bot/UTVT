"""Telegram alert service for sending trading signals."""

import asyncio
from datetime import datetime

from telegram import Bot
from telegram.constants import ParseMode

from bot.config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from bot.strategies.scalping import Signal


def _format_signal(signal: Signal) -> str:
    """
    Format a trading signal into a Telegram message.

    Args:
        signal: The trading Signal to format.

    Returns:
        Formatted HTML message string.
    """
    emoji = "\U0001f7e2" if signal.action == "COMPRA" else "\U0001f534"
    trend = "\U0001f4c8" if signal.action == "COMPRA" else "\U0001f4c9"

    indicators_text = "\n".join(
        f"   \u2022 {desc}" for desc in signal.indicators.values()
    )

    message = (
        f"{emoji} <b>ALERTA DE {signal.action}</b> {trend}\n"
        f"\n"
        f"\U0001f4b9 <b>Ticker:</b> {signal.ticker}\n"
        f"\U0001f4b0 <b>Precio:</b> ${signal.price:,.2f}\n"
        f"\U0001f3af <b>Confianza:</b> {signal.confidence_pct}\n"
        f"\n"
        f"\U0001f6d1 <b>Stop Loss:</b> ${signal.stop_loss:,.2f}\n"
        f"\u2705 <b>Take Profit:</b> ${signal.take_profit:,.2f}\n"
        f"\n"
        f"\U0001f4ca <b>Indicadores:</b>\n"
        f"{indicators_text}\n"
        f"\n"
        f"\U0001f552 <i>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>\n"
        f"\n"
        f"\u26a0\ufe0f <i>Esto no es asesoramiento financiero. "
        f"Opera bajo tu propio riesgo.</i>"
    )
    return message


def _format_summary(signals: list[Signal], tickers_analyzed: int) -> str:
    """
    Format a summary message for all signals found.

    Args:
        signals: List of trading signals.
        tickers_analyzed: Total number of tickers analyzed.

    Returns:
        Formatted HTML summary string.
    """
    buy_count = sum(1 for s in signals if s.action == "COMPRA")
    sell_count = sum(1 for s in signals if s.action == "VENTA")

    message = (
        f"\U0001f4cb <b>RESUMEN DE ANALISIS</b>\n"
        f"\n"
        f"\U0001f50d Tickers analizados: {tickers_analyzed}\n"
        f"\U0001f4e2 Alertas generadas: {len(signals)}\n"
        f"\U0001f7e2 Compras: {buy_count}\n"
        f"\U0001f534 Ventas: {sell_count}\n"
        f"\n"
        f"\U0001f552 <i>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>"
    )
    return message


async def _send_message_async(text: str) -> bool:
    """
    Send a message to the Telegram group asynchronously.

    Args:
        text: HTML formatted message text.

    Returns:
        True if message was sent successfully, False otherwise.
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print(
            f"[{datetime.now()}] Telegram credentials not configured. "
            f"Skipping alert."
        )
        print(f"Message content:\n{text}\n")
        return False

    try:
        bot = Bot(token=TELEGRAM_BOT_TOKEN)
        await bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=text,
            parse_mode=ParseMode.HTML,
        )
        return True
    except Exception as e:
        print(f"[{datetime.now()}] Error sending Telegram message: {e}")
        return False


def send_signal_alert(signal: Signal) -> bool:
    """
    Send a trading signal alert to the Telegram group.

    Args:
        signal: The trading signal to send.

    Returns:
        True if sent successfully.
    """
    message = _format_signal(signal)
    return asyncio.run(_send_message_async(message))


def send_summary(signals: list[Signal], tickers_analyzed: int) -> bool:
    """
    Send an analysis summary to the Telegram group.

    Args:
        signals: List of trading signals found.
        tickers_analyzed: Total tickers analyzed.

    Returns:
        True if sent successfully.
    """
    message = _format_summary(signals, tickers_analyzed)
    return asyncio.run(_send_message_async(message))


def send_startup_message() -> bool:
    """Send a startup notification to the Telegram group."""
    message = (
        "\U0001f916 <b>Bot de Trading Scalping Iniciado</b>\n"
        f"\n"
        f"\U0001f552 <i>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>\n"
        f"\n"
        f"El bot esta analizando los mercados y enviara alertas "
        f"cuando encuentre oportunidades de scalping."
    )
    return asyncio.run(_send_message_async(message))
