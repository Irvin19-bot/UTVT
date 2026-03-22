"""
Bot principal de Scalping para IQ Option.

Ejecuta el ciclo principal de análisis en tiempo real,
conectándose a IQ Option para obtener datos de mercado
y enviando señales de trading a Telegram.
"""

import sys
import time
import signal
import logging
from datetime import datetime

from scalping_bot.config import (
    ASSETS,
    CANDLE_PERIOD,
    CANDLE_COUNT,
    ANALYSIS_INTERVAL,
    MIN_CONFIDENCE,
    IQ_EMAIL,
    IQ_PASSWORD,
)
from scalping_bot.iq_option_client import IQOptionClient
from scalping_bot.strategy import ScalpingStrategy, SignalType
from scalping_bot.telegram_sender import TelegramSender

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("scalping_bot.log", encoding="utf-8"),
    ],
)

logger = logging.getLogger("ScalpingBot")


class ScalpingBot:
    """
    Bot de scalping que analiza el mercado en tiempo real
    y envía señales a Telegram.
    """

    def __init__(self):
        self.iq_client = IQOptionClient()
        self.strategy = ScalpingStrategy()
        self.telegram = TelegramSender()
        self.running = False
        self.signals_sent = 0
        self.analyses_done = 0
        self.start_time = None

        # Registro de señales recientes para evitar duplicados
        self._recent_signals: dict[str, float] = {}
        # Cooldown entre señales del mismo activo (en segundos)
        self._signal_cooldown = 300  # 5 minutos

    def _signal_handler(self, signum, frame):
        """Maneja señales del sistema para detener el bot."""
        logger.info("Señal de detención recibida. Cerrando bot...")
        self.running = False

    def _is_signal_on_cooldown(self, asset: str) -> bool:
        """Verifica si un activo está en período de cooldown."""
        if asset in self._recent_signals:
            elapsed = time.time() - self._recent_signals[asset]
            if elapsed < self._signal_cooldown:
                remaining = self._signal_cooldown - elapsed
                logger.debug(
                    "%s en cooldown. Faltan %.0f segundos.",
                    asset,
                    remaining,
                )
                return True
        return False

    def _register_signal(self, asset: str):
        """Registra una señal enviada para control de cooldown."""
        self._recent_signals[asset] = time.time()

    def start(self):
        """Inicia el bot de scalping."""
        logger.info("=" * 60)
        logger.info("INICIANDO SCALPING BOT v1.0")
        logger.info("=" * 60)

        # Configurar manejo de señales del sistema
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        # Verificar conexión con Telegram
        logger.info("Verificando conexión con Telegram...")
        if not self.telegram.test_connection():
            logger.error(
                "No se pudo conectar con Telegram. Verifica el token."
            )
            return

        # Conectar a IQ Option
        logger.info("Conectando a IQ Option...")
        if not self.iq_client.connect():
            logger.error(
                "No se pudo conectar a IQ Option. "
                "Verifica las credenciales."
            )
            self.telegram.send_error_message(
                "No se pudo conectar a IQ Option. "
                "Verifica las credenciales."
            )
            return

        # Enviar mensaje de inicio a Telegram
        self.telegram.send_startup_message()
        self.running = True
        self.start_time = datetime.now()

        logger.info("Bot iniciado correctamente.")
        logger.info("Activos monitoreados: %s", ", ".join(ASSETS))
        logger.info("Intervalo de análisis: %d segundos", ANALYSIS_INTERVAL)
        logger.info(
            "Confianza mínima para señal: %d%%", MIN_CONFIDENCE
        )
        logger.info("=" * 60)

        # Ciclo principal
        try:
            self._main_loop()
        except Exception as e:
            logger.critical("Error crítico en el bot: %s", str(e))
            self.telegram.send_error_message(str(e))
        finally:
            self._shutdown()

    def _main_loop(self):
        """Ciclo principal de análisis del mercado."""
        while self.running:
            cycle_start = time.time()

            for asset in ASSETS:
                if not self.running:
                    break

                try:
                    self._analyze_asset(asset)
                except Exception as e:
                    logger.error(
                        "Error al analizar %s: %s", asset, str(e)
                    )

            self.analyses_done += 1

            # Mostrar estadísticas periódicamente
            if self.analyses_done % 12 == 0:
                self._log_stats()

            # Esperar hasta el próximo ciclo
            elapsed = time.time() - cycle_start
            wait_time = max(0, ANALYSIS_INTERVAL - elapsed)
            if wait_time > 0 and self.running:
                time.sleep(wait_time)

    def _analyze_asset(self, asset: str):
        """
        Analiza un activo específico.

        Args:
            asset: Nombre del activo a analizar.
        """
        # Verificar cooldown
        if self._is_signal_on_cooldown(asset):
            return

        # Verificar si el activo está disponible
        if not self.iq_client.check_asset_open(asset):
            logger.debug("%s no disponible actualmente.", asset)
            return

        # Obtener velas
        df = self.iq_client.get_candles(
            asset, CANDLE_PERIOD, CANDLE_COUNT
        )
        if df is None:
            return

        # Analizar con la estrategia
        signal_result = self.strategy.analyze(asset, df)

        if signal_result and signal_result.signal_type != SignalType.NEUTRAL:
            logger.info(
                "=" * 40 + " SEÑAL DETECTADA " + "=" * 40
            )
            logger.info(
                "Activo: %s | Tipo: %s | Confianza: %.1f%%",
                signal_result.asset,
                signal_result.signal_type.value,
                signal_result.confidence,
            )

            # Enviar señal a Telegram
            if self.telegram.send_signal(signal_result):
                self.signals_sent += 1
                self._register_signal(asset)
                logger.info(
                    "Señal enviada a Telegram. Total: %d",
                    self.signals_sent,
                )
            else:
                logger.error(
                    "Error al enviar señal de %s a Telegram.", asset
                )

    def _log_stats(self):
        """Registra estadísticas del bot."""
        if self.start_time:
            uptime = datetime.now() - self.start_time
            logger.info(
                "📊 Estadísticas: Tiempo activo: %s | "
                "Ciclos: %d | Señales enviadas: %d",
                str(uptime).split(".")[0],
                self.analyses_done,
                self.signals_sent,
            )

    def _shutdown(self):
        """Detiene el bot de forma ordenada."""
        logger.info("Deteniendo bot...")
        self.telegram.send_shutdown_message()
        self.iq_client.disconnect()

        if self.start_time:
            uptime = datetime.now() - self.start_time
            logger.info("Tiempo total activo: %s", str(uptime).split(".")[0])

        logger.info("Señales enviadas en esta sesión: %d", self.signals_sent)
        logger.info("Bot detenido correctamente.")


def main():
    """Punto de entrada principal."""
    print(
        "\n"
        "╔══════════════════════════════════════════╗\n"
        "║     SCALPING TRADING BOT v1.0            ║\n"
        "║     Broker: IQ Option                    ║\n"
        "║     Señales: Telegram                    ║\n"
        "╚══════════════════════════════════════════╝\n"
    )

    # Verificar credenciales
    if not IQ_EMAIL or not IQ_PASSWORD:
        print(
            "\n❌ ERROR: Credenciales de IQ Option no configuradas.\n"
            "\nConfigura las siguientes variables de entorno:\n"
            "  export IQ_OPTION_EMAIL='tu_email@ejemplo.com'\n"
            "  export IQ_OPTION_PASSWORD='tu_contraseña'\n"
            "\nO créalas en un archivo .env en el directorio raíz.\n"
        )
        sys.exit(1)

    bot = ScalpingBot()
    bot.start()


if __name__ == "__main__":
    main()
