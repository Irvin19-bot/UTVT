"""
Módulo de conexión con IQ Option.
Gestiona la conexión al broker y la obtención de datos de mercado en tiempo real.
"""

import time
import logging
from typing import Optional

import pandas as pd
from iqoptionapi.stable_api import IQ_Option

from scalping_bot.config import (
    IQ_EMAIL,
    IQ_PASSWORD,
    IQ_ACCOUNT_TYPE,
    CANDLE_PERIOD,
    CANDLE_COUNT,
)

logger = logging.getLogger(__name__)


class IQOptionClient:
    """Cliente para conexión con IQ Option."""

    def __init__(self, email: str = "", password: str = ""):
        self.email = email or IQ_EMAIL
        self.password = password or IQ_PASSWORD
        self.api: Optional[IQ_Option] = None
        self.connected = False

    def connect(self, max_retries: int = 3) -> bool:
        """
        Establece conexión con IQ Option.

        Args:
            max_retries: Número máximo de intentos de conexión.

        Returns:
            True si la conexión fue exitosa, False en caso contrario.
        """
        if not self.email or not self.password:
            logger.error(
                "Credenciales de IQ Option no configuradas. "
                "Establece IQ_OPTION_EMAIL e IQ_OPTION_PASSWORD."
            )
            return False

        for attempt in range(1, max_retries + 1):
            try:
                logger.info(
                    "Intentando conectar a IQ Option (intento %d/%d)...",
                    attempt,
                    max_retries,
                )
                self.api = IQ_Option(self.email, self.password)
                check, reason = self.api.connect()

                if check:
                    self.connected = True
                    self.api.change_balance(IQ_ACCOUNT_TYPE)
                    balance = self.api.get_balance()
                    logger.info(
                        "Conectado exitosamente a IQ Option. "
                        "Cuenta: %s | Balance: $%.2f",
                        IQ_ACCOUNT_TYPE,
                        balance,
                    )
                    return True
                else:
                    logger.warning(
                        "Fallo al conectar (intento %d): %s",
                        attempt,
                        reason,
                    )
            except Exception as e:
                logger.error(
                    "Error de conexión (intento %d): %s",
                    attempt,
                    str(e),
                )

            if attempt < max_retries:
                wait_time = attempt * 5
                logger.info("Reintentando en %d segundos...", wait_time)
                time.sleep(wait_time)

        logger.error(
            "No se pudo conectar a IQ Option después de %d intentos.",
            max_retries,
        )
        return False

    def disconnect(self):
        """Desconecta del broker."""
        if self.api:
            try:
                self.api.disconnect()
                self.connected = False
                logger.info("Desconectado de IQ Option.")
            except Exception as e:
                logger.error("Error al desconectar: %s", str(e))

    def get_candles(
        self,
        asset: str,
        period: int = CANDLE_PERIOD,
        count: int = CANDLE_COUNT,
    ) -> Optional[pd.DataFrame]:
        """
        Obtiene velas históricas para un activo.

        Args:
            asset: Nombre del activo (ej: "EURUSD").
            period: Período de la vela en segundos.
            count: Número de velas a obtener.

        Returns:
            DataFrame con columnas: open, close, high, low, volume, timestamp.
            None si hay error.
        """
        if not self.connected or not self.api:
            logger.error("No hay conexión activa con IQ Option.")
            return None

        try:
            candles = self.api.get_candles(asset, period, count, time.time())

            if not candles:
                logger.warning("No se obtuvieron velas para %s.", asset)
                return None

            df = pd.DataFrame(candles)
            df = df.rename(
                columns={
                    "open": "open",
                    "close": "close",
                    "max": "high",
                    "min": "low",
                    "volume": "volume",
                    "from": "timestamp",
                }
            )

            # Asegurar que las columnas necesarias existan
            required_cols = ["open", "close", "high", "low", "volume"]
            for col in required_cols:
                if col not in df.columns:
                    logger.warning(
                        "Columna '%s' no encontrada en datos de %s.",
                        col,
                        asset,
                    )
                    return None

            # Convertir a tipos numéricos
            for col in required_cols:
                df[col] = pd.to_numeric(df[col], errors="coerce")

            df = df.sort_values("timestamp").reset_index(drop=True)

            logger.debug(
                "Obtenidas %d velas para %s.", len(df), asset
            )
            return df

        except Exception as e:
            logger.error(
                "Error al obtener velas de %s: %s", asset, str(e)
            )
            return None

    def check_asset_open(self, asset: str) -> bool:
        """
        Verifica si un activo está disponible para operar.

        Args:
            asset: Nombre del activo.

        Returns:
            True si el activo está abierto para operaciones.
        """
        if not self.connected or not self.api:
            return False

        try:
            all_assets = self.api.get_all_open_time()
            # Buscar en opciones binarias y digitales
            for market_type in ["turbo", "binary", "digital"]:
                if market_type in all_assets:
                    asset_info = all_assets[market_type].get(asset, {})
                    if asset_info.get("open", False):
                        return True
            return False
        except Exception as e:
            logger.error(
                "Error al verificar estado de %s: %s", asset, str(e)
            )
            return False

    def get_current_price(self, asset: str) -> Optional[float]:
        """
        Obtiene el precio actual de un activo.

        Args:
            asset: Nombre del activo.

        Returns:
            Precio actual o None si hay error.
        """
        if not self.connected or not self.api:
            return None

        try:
            candles = self.api.get_candles(asset, 60, 1, time.time())
            if candles:
                return float(candles[0]["close"])
            return None
        except Exception as e:
            logger.error(
                "Error al obtener precio de %s: %s", asset, str(e)
            )
            return None

    def get_balance(self) -> float:
        """Obtiene el balance actual de la cuenta."""
        if not self.connected or not self.api:
            return 0.0
        try:
            return float(self.api.get_balance())
        except Exception:
            return 0.0
