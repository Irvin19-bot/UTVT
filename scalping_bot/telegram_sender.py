"""
Módulo para enviar señales de trading a un grupo de Telegram.
"""

import logging
from datetime import datetime

import requests

from scalping_bot.config import TELEGRAM_BOT_TOKEN, TELEGRAM_GROUP_ID
from scalping_bot.strategy import TradingSignal, SignalType

logger = logging.getLogger(__name__)


class TelegramSender:
    """Envía mensajes y señales de trading a un grupo de Telegram."""

    BASE_URL = "https://api.telegram.org/bot{token}"

    def __init__(
        self,
        token: str = "",
        group_id: int = 0,
    ):
        self.token = token or TELEGRAM_BOT_TOKEN
        self.group_id = group_id or TELEGRAM_GROUP_ID
        self.api_url = self.BASE_URL.format(token=self.token)

    def send_message(self, text: str, parse_mode: str = "HTML") -> bool:
        """
        Envía un mensaje de texto al grupo de Telegram.

        Args:
            text: Texto del mensaje (soporta HTML).
            parse_mode: Modo de parseo ("HTML" o "Markdown").

        Returns:
            True si el mensaje se envió correctamente.
        """
        url = f"{self.api_url}/sendMessage"
        payload = {
            "chat_id": self.group_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": True,
        }

        try:
            response = requests.post(url, json=payload, timeout=10)
            result = response.json()

            if result.get("ok"):
                logger.info("Mensaje enviado a Telegram exitosamente.")
                return True
            else:
                logger.error(
                    "Error al enviar mensaje a Telegram: %s",
                    result.get("description", "Error desconocido"),
                )
                return False
        except requests.exceptions.RequestException as e:
            logger.error(
                "Error de conexión con Telegram: %s", str(e)
            )
            return False

    def format_signal(self, signal: TradingSignal) -> str:
        """
        Formatea una señal de trading como mensaje HTML para Telegram.

        Args:
            signal: Señal de trading a formatear.

        Returns:
            Mensaje formateado en HTML.
        """
        if signal.signal_type == SignalType.CALL:
            header = "🟢 <b>SEÑAL DE COMPRA (CALL)</b> 🟢"
            direction = "⬆️ ALCISTA"
        elif signal.signal_type == SignalType.PUT:
            header = "🔴 <b>SEÑAL DE VENTA (PUT)</b> 🔴"
            direction = "⬇️ BAJISTA"
        else:
            header = "⚪ <b>NEUTRAL</b> ⚪"
            direction = "➡️ LATERAL"

        # Barra de confianza visual
        filled = int(signal.confidence / 10)
        empty = 10 - filled
        confidence_bar = "🟩" * filled + "⬜" * empty

        message = (
            f"{header}\n"
            f"{'━' * 28}\n\n"
            f"📊 <b>Activo:</b> {signal.asset}\n"
            f"💰 <b>Precio actual:</b> {signal.current_price}\n"
            f"📈 <b>Dirección:</b> {direction}\n"
            f"🎯 <b>Confianza:</b> {signal.confidence}%\n"
            f"{confidence_bar}\n\n"
            f"{'━' * 28}\n"
            f"<b>📋 ANÁLISIS TÉCNICO</b>\n"
            f"{'━' * 28}\n\n"
            f"📉 <b>RSI ({signal.rsi_value}):</b> "
            f"{'Sobreventa' if signal.rsi_value < 30 else 'Sobrecompra' if signal.rsi_value > 70 else 'Normal'}\n"
            f"📊 <b>EMA:</b> {signal.ema_signal}\n"
            f"📏 <b>Bollinger:</b> {signal.bb_signal}\n"
            f"📐 <b>MACD:</b> {signal.macd_signal}\n"
            f"📊 <b>Volumen:</b> {signal.volume_signal}\n\n"
            f"{'━' * 28}\n"
            f"<b>🎯 NIVELES CLAVE</b>\n"
            f"{'━' * 28}\n\n"
            f"🟢 <b>Soporte:</b> {signal.support_level}\n"
            f"🔴 <b>Resistencia:</b> {signal.resistance_level}\n"
            f"🛑 <b>Stop Loss:</b> {signal.stop_loss}\n"
            f"✅ <b>Take Profit:</b> {signal.take_profit}\n\n"
            f"{'━' * 28}\n"
            f"⏰ <b>Hora:</b> {signal.timestamp}\n"
            f"⚠️ <i>Señal generada automáticamente.\n"
            f"Opere bajo su propio riesgo.</i>\n"
            f"{'━' * 28}\n"
            f"🤖 <b>Scalping Bot v1.0</b>"
        )

        return message

    def send_signal(self, signal: TradingSignal) -> bool:
        """
        Envía una señal de trading formateada al grupo de Telegram.

        Args:
            signal: Señal de trading a enviar.

        Returns:
            True si se envió correctamente.
        """
        message = self.format_signal(signal)
        return self.send_message(message)

    def send_startup_message(self) -> bool:
        """Envía un mensaje de inicio del bot."""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message = (
            "🤖 <b>SCALPING BOT INICIADO</b> 🤖\n"
            f"{'━' * 28}\n\n"
            f"⏰ <b>Hora de inicio:</b> {now}\n"
            f"📊 <b>Estrategia:</b> Scalping Multi-Indicador\n"
            f"📈 <b>Indicadores:</b> RSI, EMA, BB, MACD\n"
            f"🔍 <b>Estado:</b> Analizando mercado en vivo...\n\n"
            f"<i>Se enviarán señales cuando se detecten\n"
            f"oportunidades de alta probabilidad.</i>\n"
            f"{'━' * 28}"
        )
        return self.send_message(message)

    def send_shutdown_message(self) -> bool:
        """Envía un mensaje de detención del bot."""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message = (
            "🛑 <b>SCALPING BOT DETENIDO</b> 🛑\n"
            f"{'━' * 28}\n\n"
            f"⏰ <b>Hora de detención:</b> {now}\n"
            f"<i>El bot ha dejado de analizar el mercado.</i>\n"
            f"{'━' * 28}"
        )
        return self.send_message(message)

    def send_error_message(self, error: str) -> bool:
        """Envía un mensaje de error al grupo."""
        message = (
            "⚠️ <b>ERROR EN EL BOT</b> ⚠️\n"
            f"{'━' * 28}\n\n"
            f"❌ <b>Error:</b> {error}\n\n"
            f"<i>El bot intentará recuperarse automáticamente.</i>\n"
            f"{'━' * 28}"
        )
        return self.send_message(message)

    def test_connection(self) -> bool:
        """
        Prueba la conexión con la API de Telegram.

        Returns:
            True si la conexión es exitosa.
        """
        url = f"{self.api_url}/getMe"
        try:
            response = requests.get(url, timeout=10)
            result = response.json()
            if result.get("ok"):
                bot_name = result["result"].get("first_name", "Unknown")
                logger.info(
                    "Conexión con Telegram exitosa. Bot: %s", bot_name
                )
                return True
            else:
                logger.error(
                    "Error al conectar con Telegram: %s",
                    result.get("description", "Error desconocido"),
                )
                return False
        except requests.exceptions.RequestException as e:
            logger.error("Error de conexión con Telegram: %s", str(e))
            return False
