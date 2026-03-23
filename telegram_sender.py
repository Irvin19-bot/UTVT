"""
Modulo de envio de senales a Telegram
=====================================
Envia senales de compra/venta al grupo de Telegram configurado.
"""

import logging
from datetime import datetime

import requests

import config

logger = logging.getLogger(__name__)


class TelegramSender:
    """Envia senales de trading al grupo de Telegram."""

    def __init__(self, token=None, chat_id=None):
        self.token = token or config.TELEGRAM_TOKEN
        self.chat_id = chat_id or config.TELEGRAM_CHAT_ID
        self.base_url = f"https://api.telegram.org/bot{self.token}"
        self.signals_sent = 0

    def send_message(self, message):
        """Envia un mensaje al grupo de Telegram."""
        url = f"{self.base_url}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "HTML",
        }
        try:
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code == 200:
                logger.info("Mensaje enviado a Telegram exitosamente")
                return True
            else:
                logger.error(
                    "Error al enviar mensaje a Telegram: %s - %s",
                    response.status_code,
                    response.text,
                )
                return False
        except requests.RequestException as e:
            logger.error("Error de conexion con Telegram: %s", e)
            return False

    def send_signal(self, signal_data):
        """
        Envia una senal de trading formateada al grupo.

        Args:
            signal_data (dict): Diccionario con los datos de la senal:
                - asset: Par de divisas (ej: EURUSD)
                - direction: "CALL" (compra) o "PUT" (venta)
                - confidence: Porcentaje de confianza
                - expiration: Tiempo de expiracion en minutos
                - indicators: Dict con los valores de indicadores
                - price: Precio actual
        """
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        direction = signal_data.get("direction", "N/A")
        asset = signal_data.get("asset", "N/A")
        confidence = signal_data.get("confidence", 0)
        expiration = signal_data.get("expiration", config.EXPIRATION_TIME)
        price = signal_data.get("price", "N/A")
        indicators = signal_data.get("indicators", {})

        if direction == "CALL":
            emoji_dir = "\U0001f7e2"  # Green circle
            action = "COMPRA (CALL)"
        else:
            emoji_dir = "\U0001f534"  # Red circle
            action = "VENTA (PUT)"

        # Construir indicadores string
        indicators_text = ""
        if indicators:
            if "rsi" in indicators:
                indicators_text += f"   RSI: {indicators['rsi']:.2f}\n"
            if "macd" in indicators:
                indicators_text += f"   MACD: {indicators['macd']:.4f}\n"
            if "macd_signal" in indicators:
                indicators_text += (
                    f"   MACD Signal: {indicators['macd_signal']:.4f}\n"
                )
            if "ema_fast" in indicators:
                indicators_text += f"   EMA Rapida({config.EMA_FAST}): {indicators['ema_fast']:.5f}\n"
            if "ema_slow" in indicators:
                indicators_text += f"   EMA Lenta({config.EMA_SLOW}): {indicators['ema_slow']:.5f}\n"
            if "bb_upper" in indicators:
                indicators_text += (
                    f"   BB Superior: {indicators['bb_upper']:.5f}\n"
                )
            if "bb_lower" in indicators:
                indicators_text += (
                    f"   BB Inferior: {indicators['bb_lower']:.5f}\n"
                )
            if "stoch_k" in indicators:
                indicators_text += f"   Stoch %K: {indicators['stoch_k']:.2f}\n"
            if "stoch_d" in indicators:
                indicators_text += f"   Stoch %D: {indicators['stoch_d']:.2f}\n"

        # Barra de confianza
        filled = int(confidence / 10)
        empty = 10 - filled
        confidence_bar = "\u2588" * filled + "\u2591" * empty

        message = (
            f"{emoji_dir} <b>SENAL DE SCALPING</b> {emoji_dir}\n"
            f"{'=' * 30}\n"
            f"\n"
            f"\U0001f4b1 <b>Par:</b> {asset}\n"
            f"\U0001f3af <b>Accion:</b> {action}\n"
            f"\U0001f4b0 <b>Precio:</b> {price}\n"
            f"\u23f0 <b>Expiracion:</b> {expiration} minutos\n"
            f"\U0001f4ca <b>Confianza:</b> {confidence:.1f}% [{confidence_bar}]\n"
            f"\n"
            f"\U0001f4c8 <b>Indicadores:</b>\n"
            f"{indicators_text}\n"
            f"\U0001f552 <b>Hora:</b> {now}\n"
            f"{'=' * 30}\n"
            f"\u26a0\ufe0f <i>Senal automatica - Usar bajo su propia responsabilidad</i>"
        )

        result = self.send_message(message)
        if result:
            self.signals_sent += 1
        return result

    def send_startup_message(self):
        """Envia mensaje de inicio del bot."""
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        message = (
            f"\U0001f916 <b>Bot de Scalping Iniciado</b>\n"
            f"{'=' * 30}\n"
            f"\n"
            f"\U0001f4ca <b>Estrategia:</b> Scalping Multi-Indicador\n"
            f"\u23f0 <b>Expiracion:</b> {config.EXPIRATION_TIME} minutos\n"
            f"\U0001f4b0 <b>Inversion:</b> ${config.INVESTMENT_AMOUNT}\n"
            f"\U0001f4b1 <b>Pares:</b> {', '.join(config.ASSETS)}\n"
            f"\U0001f3af <b>Confianza minima:</b> {config.MIN_CONFIDENCE}%\n"
            f"\U0001f552 <b>Hora inicio:</b> {now}\n"
            f"\n"
            f"\U0001f4c8 <b>Indicadores:</b>\n"
            f"   - RSI ({config.RSI_PERIOD})\n"
            f"   - Bollinger Bands ({config.BB_PERIOD}, {config.BB_STD_DEV})\n"
            f"   - EMA ({config.EMA_FAST}/{config.EMA_SLOW})\n"
            f"   - MACD ({config.MACD_FAST}/{config.MACD_SLOW}/{config.MACD_SIGNAL})\n"
            f"   - Stochastic ({config.STOCH_K}/{config.STOCH_D})\n"
            f"\n"
            f"\u26a0\ufe0f <i>Modo: {'DEMO' if config.ACCOUNT_TYPE == 'PRACTICE' else 'REAL'}</i>\n"
            f"\u26a0\ufe0f <i>Trading conlleva riesgos. Use bajo su responsabilidad.</i>"
        )
        return self.send_message(message)

    def send_result_message(self, asset, direction, result, profit):
        """Envia el resultado de una operacion."""
        if result == "win":
            emoji = "\u2705"
            result_text = "GANADA"
        elif result == "loss":
            emoji = "\u274c"
            result_text = "PERDIDA"
        else:
            emoji = "\u2796"
            result_text = "EMPATE"

        message = (
            f"{emoji} <b>Resultado de Operacion</b>\n"
            f"{'=' * 30}\n"
            f"\U0001f4b1 <b>Par:</b> {asset}\n"
            f"\U0001f3af <b>Direccion:</b> {direction}\n"
            f"\U0001f4ca <b>Resultado:</b> {result_text}\n"
            f"\U0001f4b0 <b>Ganancia/Perdida:</b> ${profit:.2f}\n"
        )
        return self.send_message(message)

    def send_shutdown_message(self, stats=None):
        """Envia mensaje de apagado del bot."""
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        stats_text = ""
        if stats:
            stats_text = (
                f"\n\U0001f4ca <b>Estadisticas de la sesion:</b>\n"
                f"   Senales enviadas: {stats.get('signals', 0)}\n"
                f"   Operaciones: {stats.get('operations', 0)}\n"
                f"   Ganadas: {stats.get('wins', 0)}\n"
                f"   Perdidas: {stats.get('losses', 0)}\n"
                f"   Ganancia neta: ${stats.get('net_profit', 0):.2f}\n"
            )

        message = (
            f"\U0001f6d1 <b>Bot de Scalping Detenido</b>\n"
            f"{'=' * 30}\n"
            f"\U0001f552 <b>Hora:</b> {now}\n"
            f"{stats_text}"
        )
        return self.send_message(message)
