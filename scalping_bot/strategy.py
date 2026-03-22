"""
Estrategia de Scalping con múltiples indicadores técnicos.

Utiliza una combinación de:
- RSI (Relative Strength Index)
- EMA (Exponential Moving Average) cruce rápida/lenta
- Bollinger Bands
- MACD (Moving Average Convergence Divergence)
- Análisis de volumen

Para generar señales de compra (CALL) o venta (PUT) con un nivel de confianza.
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Optional

import pandas as pd
import ta

from scalping_bot.config import (
    RSI_PERIOD,
    RSI_OVERBOUGHT,
    RSI_OVERSOLD,
    EMA_FAST,
    EMA_SLOW,
    BB_PERIOD,
    BB_STD_DEV,
    MACD_FAST,
    MACD_SLOW,
    MACD_SIGNAL,
    MIN_CONFIDENCE,
)

logger = logging.getLogger(__name__)


class SignalType(Enum):
    """Tipo de señal de trading."""
    CALL = "COMPRA (CALL) 📈"
    PUT = "VENTA (PUT) 📉"
    NEUTRAL = "NEUTRAL ⏸️"


@dataclass
class TradingSignal:
    """Estructura de una señal de trading."""
    asset: str
    signal_type: SignalType
    confidence: float
    current_price: float
    rsi_value: float
    ema_signal: str
    bb_signal: str
    macd_signal: str
    volume_signal: str
    support_level: float
    resistance_level: float
    stop_loss: float
    take_profit: float
    timestamp: str


class ScalpingStrategy:
    """
    Estrategia de Scalping que combina múltiples indicadores técnicos
    para generar señales de alta probabilidad.
    """

    def __init__(self):
        self.rsi_period = RSI_PERIOD
        self.rsi_overbought = RSI_OVERBOUGHT
        self.rsi_oversold = RSI_OVERSOLD
        self.ema_fast = EMA_FAST
        self.ema_slow = EMA_SLOW
        self.bb_period = BB_PERIOD
        self.bb_std = BB_STD_DEV
        self.macd_fast = MACD_FAST
        self.macd_slow = MACD_SLOW
        self.macd_signal_period = MACD_SIGNAL
        self.min_confidence = MIN_CONFIDENCE

    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calcula todos los indicadores técnicos sobre el DataFrame de velas.

        Args:
            df: DataFrame con columnas open, high, low, close, volume.

        Returns:
            DataFrame con indicadores calculados.
        """
        data = df.copy()

        # RSI
        data["rsi"] = ta.momentum.RSIIndicator(
            close=data["close"], window=self.rsi_period
        ).rsi()

        # EMA rápida y lenta
        data["ema_fast"] = ta.trend.EMAIndicator(
            close=data["close"], window=self.ema_fast
        ).ema_indicator()

        data["ema_slow"] = ta.trend.EMAIndicator(
            close=data["close"], window=self.ema_slow
        ).ema_indicator()

        # Bollinger Bands
        bb = ta.volatility.BollingerBands(
            close=data["close"],
            window=self.bb_period,
            window_dev=self.bb_std,
        )
        data["bb_upper"] = bb.bollinger_hband()
        data["bb_middle"] = bb.bollinger_mavg()
        data["bb_lower"] = bb.bollinger_lband()
        data["bb_width"] = bb.bollinger_wband()

        # MACD
        macd = ta.trend.MACD(
            close=data["close"],
            window_fast=self.macd_fast,
            window_slow=self.macd_slow,
            window_sign=self.macd_signal_period,
        )
        data["macd"] = macd.macd()
        data["macd_signal"] = macd.macd_signal()
        data["macd_histogram"] = macd.macd_diff()

        # Stochastic RSI para confirmación adicional
        stoch_rsi = ta.momentum.StochRSIIndicator(
            close=data["close"], window=14, smooth1=3, smooth2=3
        )
        data["stoch_rsi_k"] = stoch_rsi.stochrsi_k()
        data["stoch_rsi_d"] = stoch_rsi.stochrsi_d()

        # ATR para gestión de riesgo
        atr = ta.volatility.AverageTrueRange(
            high=data["high"],
            low=data["low"],
            close=data["close"],
            window=14,
        )
        data["atr"] = atr.average_true_range()

        # Media de volumen
        data["volume_sma"] = data["volume"].rolling(window=20).mean()

        return data

    def _analyze_rsi(self, data: pd.DataFrame) -> tuple[str, float]:
        """Analiza la señal del RSI."""
        rsi = data["rsi"].iloc[-1]
        prev_rsi = data["rsi"].iloc[-2]

        if rsi < self.rsi_oversold:
            if rsi < prev_rsi:
                return "SOBREVENTA FUERTE", 20
            return "SOBREVENTA", 15
        elif rsi > self.rsi_overbought:
            if rsi > prev_rsi:
                return "SOBRECOMPRA FUERTE", -20
            return "SOBRECOMPRA", -15
        elif 40 <= rsi <= 60:
            return "NEUTRAL", 0
        elif rsi < 40:
            return "TENDENCIA BAJISTA", 5
        else:
            return "TENDENCIA ALCISTA", -5

    def _analyze_ema(self, data: pd.DataFrame) -> tuple[str, float]:
        """Analiza el cruce de EMAs."""
        ema_f = data["ema_fast"].iloc[-1]
        ema_s = data["ema_slow"].iloc[-1]
        prev_ema_f = data["ema_fast"].iloc[-2]
        prev_ema_s = data["ema_slow"].iloc[-2]

        # Cruce alcista
        if prev_ema_f <= prev_ema_s and ema_f > ema_s:
            return "CRUCE ALCISTA", 25
        # Cruce bajista
        elif prev_ema_f >= prev_ema_s and ema_f < ema_s:
            return "CRUCE BAJISTA", -25
        # EMA rápida por encima (tendencia alcista)
        elif ema_f > ema_s:
            gap = (ema_f - ema_s) / ema_s * 100
            return f"ALCISTA (gap: {gap:.4f}%)", 10
        # EMA rápida por debajo (tendencia bajista)
        else:
            gap = (ema_s - ema_f) / ema_s * 100
            return f"BAJISTA (gap: {gap:.4f}%)", -10

    def _analyze_bollinger(self, data: pd.DataFrame) -> tuple[str, float]:
        """Analiza las Bandas de Bollinger."""
        close = data["close"].iloc[-1]
        upper = data["bb_upper"].iloc[-1]
        lower = data["bb_lower"].iloc[-1]
        middle = data["bb_middle"].iloc[-1]

        # Precio tocando banda inferior (posible rebote alcista)
        if close <= lower:
            return "TOCA BANDA INFERIOR", 20
        # Precio tocando banda superior (posible rebote bajista)
        elif close >= upper:
            return "TOCA BANDA SUPERIOR", -20
        # Precio entre media y banda inferior
        elif close < middle:
            proximity = (middle - close) / (middle - lower) * 100
            if proximity > 70:
                return "CERCA BANDA INFERIOR", 10
            return "BAJO MEDIA", 5
        # Precio entre media y banda superior
        else:
            proximity = (close - middle) / (upper - middle) * 100
            if proximity > 70:
                return "CERCA BANDA SUPERIOR", -10
            return "SOBRE MEDIA", -5

    def _analyze_macd(self, data: pd.DataFrame) -> tuple[str, float]:
        """Analiza el MACD."""
        macd = data["macd"].iloc[-1]
        signal = data["macd_signal"].iloc[-1]
        histogram = data["macd_histogram"].iloc[-1]
        prev_histogram = data["macd_histogram"].iloc[-2]

        # Cruce MACD por encima de la señal
        if macd > signal and data["macd"].iloc[-2] <= data["macd_signal"].iloc[-2]:
            return "CRUCE ALCISTA", 20
        # Cruce MACD por debajo de la señal
        elif macd < signal and data["macd"].iloc[-2] >= data["macd_signal"].iloc[-2]:
            return "CRUCE BAJISTA", -20
        # Histograma creciente (momentum alcista)
        elif histogram > 0 and histogram > prev_histogram:
            return "MOMENTUM ALCISTA", 10
        # Histograma decreciente (momentum bajista)
        elif histogram < 0 and histogram < prev_histogram:
            return "MOMENTUM BAJISTA", -10
        else:
            return "NEUTRAL", 0

    def _analyze_volume(self, data: pd.DataFrame) -> tuple[str, float]:
        """Analiza el volumen."""
        current_vol = data["volume"].iloc[-1]
        avg_vol = data["volume_sma"].iloc[-1]

        if pd.isna(avg_vol) or avg_vol == 0:
            return "SIN DATOS", 0

        vol_ratio = current_vol / avg_vol

        if vol_ratio > 2.0:
            return "VOLUMEN MUY ALTO", 10
        elif vol_ratio > 1.5:
            return "VOLUMEN ALTO", 5
        elif vol_ratio < 0.5:
            return "VOLUMEN MUY BAJO", -5
        else:
            return "VOLUMEN NORMAL", 0

    def _calculate_support_resistance(
        self, data: pd.DataFrame
    ) -> tuple[float, float]:
        """Calcula niveles de soporte y resistencia."""
        highs = data["high"].tail(20)
        lows = data["low"].tail(20)

        resistance = float(highs.max())
        support = float(lows.min())

        return support, resistance

    def _calculate_risk_levels(
        self,
        current_price: float,
        atr: float,
        signal_type: SignalType,
    ) -> tuple[float, float]:
        """
        Calcula Stop Loss y Take Profit basados en ATR.

        Returns:
            (stop_loss, take_profit)
        """
        if signal_type == SignalType.CALL:
            stop_loss = current_price - (atr * 1.5)
            take_profit = current_price + (atr * 2.0)
        elif signal_type == SignalType.PUT:
            stop_loss = current_price + (atr * 1.5)
            take_profit = current_price - (atr * 2.0)
        else:
            stop_loss = current_price
            take_profit = current_price

        return round(stop_loss, 5), round(take_profit, 5)

    def analyze(self, asset: str, df: pd.DataFrame) -> Optional[TradingSignal]:
        """
        Analiza un activo y genera una señal de trading si cumple
        los criterios de confianza.

        Args:
            asset: Nombre del activo.
            df: DataFrame con datos de velas.

        Returns:
            TradingSignal si la confianza supera el mínimo, None si no.
        """
        if df is None or len(df) < 30:
            logger.warning(
                "Datos insuficientes para analizar %s (%s velas).",
                asset,
                len(df) if df is not None else 0,
            )
            return None

        try:
            data = self.calculate_indicators(df)

            # Eliminar filas con NaN en indicadores clave
            if data["rsi"].isna().all() or data["ema_fast"].isna().all():
                logger.warning(
                    "Indicadores no calculados para %s.", asset
                )
                return None

            # Analizar cada indicador
            rsi_signal, rsi_score = self._analyze_rsi(data)
            ema_signal, ema_score = self._analyze_ema(data)
            bb_signal, bb_score = self._analyze_bollinger(data)
            macd_signal, macd_score = self._analyze_macd(data)
            vol_signal, vol_score = self._analyze_volume(data)

            # Calcular puntuación total (ponderada)
            total_score = (
                rsi_score * 0.25
                + ema_score * 0.25
                + bb_score * 0.20
                + macd_score * 0.20
                + vol_score * 0.10
            )

            # Determinar tipo de señal
            if total_score > 0:
                signal_type = SignalType.CALL
                confidence = min(abs(total_score) * 4, 100)
            elif total_score < 0:
                signal_type = SignalType.PUT
                confidence = min(abs(total_score) * 4, 100)
            else:
                signal_type = SignalType.NEUTRAL
                confidence = 0

            # Solo generar señal si la confianza supera el mínimo
            if confidence < self.min_confidence:
                logger.debug(
                    "%s: Confianza insuficiente (%.1f%% < %d%%). "
                    "RSI: %s, EMA: %s, BB: %s, MACD: %s",
                    asset,
                    confidence,
                    self.min_confidence,
                    rsi_signal,
                    ema_signal,
                    bb_signal,
                    macd_signal,
                )
                return None

            current_price = float(data["close"].iloc[-1])
            rsi_value = float(data["rsi"].iloc[-1])
            atr_value = float(data["atr"].iloc[-1])
            support, resistance = self._calculate_support_resistance(data)
            stop_loss, take_profit = self._calculate_risk_levels(
                current_price, atr_value, signal_type
            )

            signal = TradingSignal(
                asset=asset,
                signal_type=signal_type,
                confidence=round(confidence, 1),
                current_price=current_price,
                rsi_value=round(rsi_value, 2),
                ema_signal=ema_signal,
                bb_signal=bb_signal,
                macd_signal=macd_signal,
                volume_signal=vol_signal,
                support_level=round(support, 5),
                resistance_level=round(resistance, 5),
                stop_loss=stop_loss,
                take_profit=take_profit,
                timestamp=pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
            )

            logger.info(
                "SEÑAL DETECTADA: %s | %s | Confianza: %.1f%%",
                asset,
                signal_type.value,
                confidence,
            )

            return signal

        except Exception as e:
            logger.error("Error al analizar %s: %s", asset, str(e))
            return None
