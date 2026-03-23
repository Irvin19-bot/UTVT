"""
Bot de Scalping para IQ Option
===============================
Bot principal que conecta con IQ Option, analiza el mercado
en tiempo real y envia senales de trading a Telegram.

Uso:
    python bot.py                    # Solo senales (no ejecuta operaciones)
    python bot.py --auto-trade       # Ejecuta operaciones automaticamente
    python bot.py --demo             # Usa cuenta demo (default)
    python bot.py --real             # Usa cuenta real (precaucion!)
"""

import argparse
import logging
import signal
import sys
import time
from datetime import datetime, timedelta

import config
from iq_connection import IQOptionConnector
from technical_analysis import TechnicalAnalysis
from telegram_sender import TelegramSender

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("scalping_bot.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger("ScalpingBot")


class ScalpingBot:
    """Bot de scalping que analiza el mercado y envia senales."""

    def __init__(self, auto_trade=False):
        self.iq = IQOptionConnector()
        self.analyzer = TechnicalAnalysis()
        self.telegram = TelegramSender()
        self.auto_trade = auto_trade
        self.running = False
        self.stats = {
            "signals": 0,
            "operations": 0,
            "wins": 0,
            "losses": 0,
            "net_profit": 0.0,
        }
        self.operations_this_hour = 0
        self.hour_start = datetime.utcnow()
        self.active_orders = []
        self.last_signals = {}  # Para evitar senales duplicadas

    def start(self):
        """Inicia el bot de scalping."""
        logger.info("=" * 50)
        logger.info("Iniciando Bot de Scalping")
        logger.info("=" * 50)

        # Conectar a IQ Option
        logger.info("Conectando a IQ Option...")
        if not self.iq.connect():
            logger.error("No se pudo conectar a IQ Option. Abortando.")
            self.telegram.send_message(
                "\u274c <b>Error:</b> No se pudo conectar a IQ Option. "
                "Verifica las credenciales."
            )
            return False

        balance = self.iq.get_balance()
        logger.info("Balance actual: $%.2f", balance if balance else 0)

        # Enviar mensaje de inicio a Telegram
        self.telegram.send_startup_message()

        # Configurar handler de senales para apagado graceful
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        self.running = True
        logger.info("Bot iniciado correctamente. Analizando mercado...")

        # Bucle principal
        self._main_loop()

        return True

    def _signal_handler(self, sig, frame):
        """Maneja senales del sistema para apagado graceful."""
        logger.info("Senal de apagado recibida. Deteniendo bot...")
        self.running = False

    def _main_loop(self):
        """Bucle principal del bot."""
        while self.running:
            try:
                # Resetear contador de operaciones cada hora
                now = datetime.utcnow()
                if now - self.hour_start > timedelta(hours=1):
                    self.operations_this_hour = 0
                    self.hour_start = now

                # Verificar conexion
                if not self.iq.connected:
                    logger.warning("Conexion perdida. Reconectando...")
                    if not self.iq.reconnect():
                        logger.error("No se pudo reconectar. Esperando 60s...")
                        time.sleep(60)
                        continue

                # Verificar resultados de operaciones activas
                self._check_active_orders()

                # Obtener activos disponibles
                open_assets = self.iq.get_open_assets()
                if not open_assets:
                    logger.warning(
                        "No hay activos disponibles. Esperando %ds...",
                        config.ANALYSIS_INTERVAL,
                    )
                    time.sleep(config.ANALYSIS_INTERVAL)
                    continue

                logger.info(
                    "Analizando %d activos: %s",
                    len(open_assets),
                    ", ".join(open_assets),
                )

                # Analizar cada activo
                for asset in open_assets:
                    if not self.running:
                        break

                    self._analyze_asset(asset)

                # Esperar antes del siguiente ciclo
                logger.info(
                    "Ciclo completado. Siguiente analisis en %ds...",
                    config.ANALYSIS_INTERVAL,
                )
                time.sleep(config.ANALYSIS_INTERVAL)

            except KeyboardInterrupt:
                logger.info("Interrupcion de teclado. Deteniendo...")
                self.running = False
            except Exception as e:
                logger.error("Error en bucle principal: %s", e, exc_info=True)
                time.sleep(10)

        # Apagado
        self._shutdown()

    def _analyze_asset(self, asset):
        """
        Analiza un activo y genera/envia senales si corresponde.

        Args:
            asset (str): Par de divisas a analizar
        """
        try:
            # Obtener velas
            candles = self.iq.get_candles(asset)
            if not candles:
                logger.warning("Sin datos de velas para %s", asset)
                return

            # Ejecutar analisis tecnico
            result = self.analyzer.analyze(candles)
            direction = result["direction"]
            confidence = result["confidence"]
            indicators = result["indicators"]

            # Verificar si hay senal valida
            if direction is None:
                logger.debug("Sin senal para %s", asset)
                return

            if confidence < config.MIN_CONFIDENCE:
                logger.info(
                    "%s: %s con %.1f%% confianza (minimo: %d%%). Ignorando.",
                    asset,
                    direction,
                    confidence,
                    config.MIN_CONFIDENCE,
                )
                return

            # Evitar senales duplicadas (misma direccion en los ultimos 5 min)
            signal_key = f"{asset}_{direction}"
            now = datetime.utcnow()
            if signal_key in self.last_signals:
                last_time = self.last_signals[signal_key]
                if now - last_time < timedelta(minutes=config.EXPIRATION_TIME):
                    logger.info(
                        "Senal duplicada para %s %s. Ignorando.", asset, direction
                    )
                    return

            # Verificar limite de operaciones por hora
            if self.operations_this_hour >= config.MAX_OPERATIONS_PER_HOUR:
                logger.warning(
                    "Limite de operaciones por hora alcanzado (%d). Ignorando senal.",
                    config.MAX_OPERATIONS_PER_HOUR,
                )
                return

            # Senal valida! Enviar a Telegram
            logger.info(
                "\u2b50 SENAL DETECTADA: %s %s con %.1f%% confianza",
                asset,
                direction,
                confidence,
            )

            current_price = indicators.get("price", "N/A")
            signal_data = {
                "asset": asset,
                "direction": direction,
                "confidence": confidence,
                "expiration": config.EXPIRATION_TIME,
                "price": current_price,
                "indicators": {
                    k: v
                    for k, v in indicators.items()
                    if v is not None and k != "price"
                },
            }

            self.telegram.send_signal(signal_data)
            self.stats["signals"] += 1
            self.last_signals[signal_key] = now

            # Ejecutar operacion automaticamente si esta habilitado
            if self.auto_trade:
                self._execute_trade(asset, direction, confidence)

        except Exception as e:
            logger.error("Error al analizar %s: %s", asset, e, exc_info=True)

    def _execute_trade(self, asset, direction, confidence):
        """
        Ejecuta una operacion en IQ Option.

        Args:
            asset (str): Par de divisas
            direction (str): "CALL" o "PUT"
            confidence (float): Nivel de confianza
        """
        try:
            amount = config.INVESTMENT_AMOUNT

            success, order_id = self.iq.buy(
                asset, amount, direction, config.EXPIRATION_TIME
            )

            if success and order_id:
                self.stats["operations"] += 1
                self.operations_this_hour += 1
                self.active_orders.append(
                    {
                        "order_id": order_id,
                        "asset": asset,
                        "direction": direction,
                        "amount": amount,
                        "time": datetime.utcnow(),
                    }
                )
                logger.info(
                    "Operacion ejecutada: %s %s $%.2f (Order: %s)",
                    direction,
                    asset,
                    amount,
                    order_id,
                )
            else:
                logger.error(
                    "Fallo al ejecutar operacion: %s %s", direction, asset
                )
                self.telegram.send_message(
                    f"\u274c Error al ejecutar operacion: {direction} {asset}"
                )

        except Exception as e:
            logger.error("Error al ejecutar trade: %s", e, exc_info=True)

    def _check_active_orders(self):
        """Verifica el resultado de operaciones activas."""
        completed = []
        for order in self.active_orders:
            order_id = order["order_id"]
            order_time = order["time"]

            # Esperar hasta que la operacion haya expirado
            elapsed = (datetime.utcnow() - order_time).total_seconds()
            if elapsed < (config.EXPIRATION_TIME * 60) + 10:
                continue

            result, profit = self.iq.check_win(order_id)

            if result == "pending":
                continue

            if result == "win":
                self.stats["wins"] += 1
                self.stats["net_profit"] += profit
            elif result == "loss":
                self.stats["losses"] += 1
                self.stats["net_profit"] += profit

            # Enviar resultado a Telegram
            self.telegram.send_result_message(
                order["asset"], order["direction"], result, profit
            )

            completed.append(order)
            logger.info(
                "Resultado: %s %s -> %s ($%.2f)",
                order["direction"],
                order["asset"],
                result.upper(),
                profit,
            )

        # Remover ordenes completadas
        for order in completed:
            self.active_orders.remove(order)

    def _shutdown(self):
        """Apaga el bot de forma segura."""
        logger.info("Apagando bot...")

        # Enviar estadisticas finales
        self.telegram.send_shutdown_message(self.stats)

        # Desconectar de IQ Option
        self.iq.disconnect()

        logger.info("Bot detenido correctamente.")
        logger.info("Estadisticas finales:")
        logger.info("  Senales enviadas: %d", self.stats["signals"])
        logger.info("  Operaciones: %d", self.stats["operations"])
        logger.info("  Ganadas: %d", self.stats["wins"])
        logger.info("  Perdidas: %d", self.stats["losses"])
        logger.info("  Ganancia neta: $%.2f", self.stats["net_profit"])


def main():
    """Punto de entrada principal."""
    parser = argparse.ArgumentParser(
        description="Bot de Scalping para IQ Option"
    )
    parser.add_argument(
        "--auto-trade",
        action="store_true",
        help="Ejecutar operaciones automaticamente (default: solo senales)",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        default=True,
        help="Usar cuenta demo (default)",
    )
    parser.add_argument(
        "--real",
        action="store_true",
        help="Usar cuenta real (precaucion!)",
    )

    args = parser.parse_args()

    # Configurar tipo de cuenta
    if args.real:
        config.ACCOUNT_TYPE = "REAL"
        logger.warning(
            "ATENCION: Usando cuenta REAL. Las operaciones afectaran dinero real."
        )
    else:
        config.ACCOUNT_TYPE = "PRACTICE"
        logger.info("Usando cuenta DEMO.")

    # Crear e iniciar bot
    bot = ScalpingBot(auto_trade=args.auto_trade)

    print("\n" + "=" * 50)
    print("   BOT DE SCALPING - IQ OPTION")
    print("=" * 50)
    print(f"   Modo: {'AUTO-TRADE' if args.auto_trade else 'SOLO SENALES'}")
    print(f"   Cuenta: {'REAL' if args.real else 'DEMO'}")
    print(f"   Expiracion: {config.EXPIRATION_TIME} minutos")
    print(f"   Pares: {', '.join(config.ASSETS)}")
    print(f"   Confianza minima: {config.MIN_CONFIDENCE}%")
    print("=" * 50 + "\n")

    bot.start()


if __name__ == "__main__":
    main()
