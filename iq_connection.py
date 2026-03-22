"""
Modulo de Conexion a IQ Option
===============================
Gestiona la conexion con el broker IQ Option,
obtiene datos de velas y ejecuta operaciones.
"""

import logging
import time

import config

logger = logging.getLogger(__name__)


class IQOptionConnector:
    """Gestiona la conexion y operaciones con IQ Option."""

    def __init__(self, email=None, password=None):
        self.email = email or config.IQ_EMAIL
        self.password = password or config.IQ_PASSWORD
        self.api = None
        self.connected = False
        self.account_type = config.ACCOUNT_TYPE

    def connect(self):
        """
        Establece conexion con IQ Option.

        Returns:
            bool: True si la conexion fue exitosa, False en caso contrario.
        """
        try:
            from iqoptionapi.stable_api import IQ_Option

            logger.info("Conectando a IQ Option con %s...", self.email)
            self.api = IQ_Option(self.email, self.password)
            check, reason = self.api.connect()

            if check:
                self.connected = True
                self.api.change_balance(self.account_type)
                balance = self.api.get_balance()
                logger.info(
                    "Conexion exitosa a IQ Option. Balance: $%.2f (%s)",
                    balance,
                    self.account_type,
                )
                return True
            else:
                logger.error("Error al conectar a IQ Option: %s", reason)
                self.connected = False
                return False

        except ImportError:
            logger.error(
                "La libreria iqoptionapi no esta instalada. "
                "Instala con: pip install -U git+https://github.com/iqoptionapi/iqoptionapi.git"
            )
            return False
        except Exception as e:
            logger.error("Error inesperado al conectar: %s", e)
            self.connected = False
            return False

    def reconnect(self, max_retries=3):
        """Intenta reconectar a IQ Option."""
        for attempt in range(1, max_retries + 1):
            logger.info(
                "Intento de reconexion %d/%d...", attempt, max_retries
            )
            if self.connect():
                return True
            time.sleep(5 * attempt)

        logger.error("No se pudo reconectar despues de %d intentos", max_retries)
        return False

    def check_connection(self):
        """Verifica si la conexion esta activa."""
        if self.api is None:
            return False
        try:
            check, _reason = self.api.connect()
            return check
        except Exception:
            return False

    def get_balance(self):
        """Obtiene el balance actual de la cuenta."""
        if not self.connected or self.api is None:
            return None
        try:
            return self.api.get_balance()
        except Exception as e:
            logger.error("Error al obtener balance: %s", e)
            return None

    def get_candles(self, asset, period=None, count=None):
        """
        Obtiene velas historicas de un activo.

        Args:
            asset (str): Par de divisas (ej: "EURUSD")
            period (int): Periodo de vela en segundos (default: 60)
            count (int): Cantidad de velas (default: config.NUM_CANDLES)

        Returns:
            list: Lista de diccionarios con datos de velas o None si falla.
        """
        if not self.connected or self.api is None:
            logger.error("No conectado a IQ Option")
            return None

        if period is None:
            period = config.CANDLE_PERIOD
        if count is None:
            count = config.NUM_CANDLES

        try:
            candles = self.api.get_candles(asset, period, count, time.time())

            if not candles:
                logger.warning("No se obtuvieron velas para %s", asset)
                return None

            formatted_candles = []
            for candle in candles:
                formatted_candles.append(
                    {
                        "open": candle["open"],
                        "close": candle["close"],
                        "high": candle["max"],
                        "low": candle["min"],
                        "volume": candle.get("volume", 0),
                        "timestamp": candle["from"],
                    }
                )

            logger.info(
                "Obtenidas %d velas de %s", len(formatted_candles), asset
            )
            return formatted_candles

        except Exception as e:
            logger.error("Error al obtener velas de %s: %s", asset, e)
            return None

    def get_realtime_candles(self, asset, period=None):
        """
        Inicia la recepcion de velas en tiempo real.

        Args:
            asset (str): Par de divisas
            period (int): Periodo de vela en segundos

        Returns:
            bool: True si se inicio correctamente
        """
        if not self.connected or self.api is None:
            return False

        if period is None:
            period = config.CANDLE_PERIOD

        try:
            self.api.start_candles_stream(asset, period, count=1)
            return True
        except Exception as e:
            logger.error(
                "Error al iniciar stream de velas de %s: %s", asset, e
            )
            return False

    def stop_realtime_candles(self, asset, period=None):
        """Detiene la recepcion de velas en tiempo real."""
        if not self.connected or self.api is None:
            return

        if period is None:
            period = config.CANDLE_PERIOD

        try:
            self.api.stop_candles_stream(asset, period)
        except Exception as e:
            logger.error(
                "Error al detener stream de velas de %s: %s", asset, e
            )

    def check_asset_open(self, asset):
        """
        Verifica si un activo esta disponible para operar.

        Args:
            asset (str): Par de divisas

        Returns:
            bool: True si el activo esta abierto para trading
        """
        if not self.connected or self.api is None:
            return False

        try:
            all_assets = self.api.get_all_open_time()
            # Verificar en opciones binarias y digitales
            for option_type in ["turbo", "binary", "digital"]:
                if option_type in all_assets:
                    if asset in all_assets[option_type]:
                        if all_assets[option_type][asset].get("open", False):
                            return True
            return False
        except Exception as e:
            logger.error(
                "Error al verificar disponibilidad de %s: %s", asset, e
            )
            return False

    def get_open_assets(self):
        """
        Obtiene la lista de activos abiertos para operar.

        Returns:
            list: Lista de activos disponibles
        """
        if not self.connected or self.api is None:
            return []

        try:
            all_assets = self.api.get_all_open_time()
            open_assets = []
            for asset in config.ASSETS:
                for option_type in ["turbo", "binary", "digital"]:
                    if option_type in all_assets:
                        if asset in all_assets[option_type]:
                            if all_assets[option_type][asset].get("open", False):
                                if asset not in open_assets:
                                    open_assets.append(asset)
            return open_assets
        except Exception as e:
            logger.error("Error al obtener activos abiertos: %s", e)
            return []

    def buy(self, asset, amount, direction, expiration=None):
        """
        Ejecuta una operacion de compra/venta.

        Args:
            asset (str): Par de divisas
            amount (float): Monto de la inversion
            direction (str): "call" para compra, "put" para venta
            expiration (int): Tiempo de expiracion en minutos

        Returns:
            tuple: (success: bool, order_id: int or None)
        """
        if not self.connected or self.api is None:
            logger.error("No conectado a IQ Option")
            return False, None

        if expiration is None:
            expiration = config.EXPIRATION_TIME

        try:
            direction_lower = direction.lower()
            logger.info(
                "Ejecutando operacion: %s %s $%.2f exp:%d min",
                direction_lower.upper(),
                asset,
                amount,
                expiration,
            )

            status, order_id = self.api.buy(
                amount, asset, direction_lower, expiration
            )

            if status:
                logger.info(
                    "Operacion ejecutada exitosamente. Order ID: %s", order_id
                )
                return True, order_id
            else:
                logger.error("Error al ejecutar operacion")
                return False, None

        except Exception as e:
            logger.error("Error en operacion: %s", e)
            return False, None

    def check_win(self, order_id):
        """
        Verifica el resultado de una operacion.

        Args:
            order_id: ID de la orden

        Returns:
            tuple: (result: str, profit: float)
                result: "win", "loss", "equal"
        """
        if not self.connected or self.api is None:
            return "unknown", 0

        try:
            result = self.api.check_win_v4(order_id)

            if result is None:
                return "pending", 0

            if result > 0:
                return "win", result
            elif result < 0:
                return "loss", result
            else:
                return "equal", 0

        except Exception as e:
            logger.error("Error al verificar resultado: %s", e)
            return "unknown", 0

    def get_server_time(self):
        """Obtiene la hora del servidor de IQ Option."""
        if not self.connected or self.api is None:
            return None
        try:
            return self.api.get_server_timestamp()
        except Exception as e:
            logger.error("Error al obtener hora del servidor: %s", e)
            return None

    def disconnect(self):
        """Desconecta de IQ Option."""
        if self.api is not None:
            try:
                # Stop any active streams
                for asset in config.ASSETS:
                    try:
                        self.api.stop_candles_stream(asset, config.CANDLE_PERIOD)
                    except Exception:
                        pass
            except Exception:
                pass
        self.connected = False
        self.api = None
        logger.info("Desconectado de IQ Option")
