"""
Modulo de Analisis Tecnico para Scalping
=========================================
Implementa multiples indicadores tecnicos para generar
senales de compra/venta con nivel de confianza.
"""

import logging

import numpy as np
import pandas as pd

import config

logger = logging.getLogger(__name__)


class TechnicalAnalysis:
    """Analiza datos de velas y genera senales de trading."""

    def __init__(self):
        self.rsi_period = config.RSI_PERIOD
        self.bb_period = config.BB_PERIOD
        self.bb_std = config.BB_STD_DEV
        self.ema_fast = config.EMA_FAST
        self.ema_slow = config.EMA_SLOW
        self.macd_fast = config.MACD_FAST
        self.macd_slow = config.MACD_SLOW
        self.macd_signal = config.MACD_SIGNAL

    def calculate_rsi(self, prices, period=None):
        """Calcula el Relative Strength Index (RSI)."""
        if period is None:
            period = self.rsi_period

        if len(prices) < period + 1:
            return None

        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)

        avg_gain = np.mean(gains[:period])
        avg_loss = np.mean(losses[:period])

        if avg_loss == 0:
            return 100.0

        for i in range(period, len(gains)):
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period

        if avg_loss == 0:
            return 100.0

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def calculate_ema(self, prices, period):
        """Calcula la Exponential Moving Average (EMA)."""
        if len(prices) < period:
            return None
        prices_series = pd.Series(prices)
        ema = prices_series.ewm(span=period, adjust=False).mean()
        return ema.iloc[-1]

    def calculate_bollinger_bands(self, prices, period=None, std_dev=None):
        """Calcula las Bandas de Bollinger."""
        if period is None:
            period = self.bb_period
        if std_dev is None:
            std_dev = self.bb_std

        if len(prices) < period:
            return None, None, None

        prices_series = pd.Series(prices)
        sma = prices_series.rolling(window=period).mean().iloc[-1]
        std = prices_series.rolling(window=period).std().iloc[-1]

        upper = sma + (std_dev * std)
        lower = sma - (std_dev * std)

        return upper, sma, lower

    def calculate_macd(self, prices):
        """Calcula el MACD (Moving Average Convergence Divergence)."""
        if len(prices) < self.macd_slow:
            return None, None, None

        prices_series = pd.Series(prices)
        ema_fast = prices_series.ewm(span=self.macd_fast, adjust=False).mean()
        ema_slow = prices_series.ewm(span=self.macd_slow, adjust=False).mean()

        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=self.macd_signal, adjust=False).mean()
        histogram = macd_line - signal_line

        return macd_line.iloc[-1], signal_line.iloc[-1], histogram.iloc[-1]

    def calculate_stochastic(self, highs, lows, closes, k_period=None, d_period=None):
        """Calcula el Oscilador Estocastico."""
        if k_period is None:
            k_period = config.STOCH_K
        if d_period is None:
            d_period = config.STOCH_D

        if len(closes) < k_period:
            return None, None

        highs_series = pd.Series(highs)
        lows_series = pd.Series(lows)
        closes_series = pd.Series(closes)

        lowest_low = lows_series.rolling(window=k_period).min()
        highest_high = highs_series.rolling(window=k_period).max()

        denominator = highest_high - lowest_low
        denominator = denominator.replace(0, np.nan)

        stoch_k = ((closes_series - lowest_low) / denominator) * 100
        stoch_d = stoch_k.rolling(window=d_period).mean()

        return stoch_k.iloc[-1], stoch_d.iloc[-1]

    def calculate_atr(self, highs, lows, closes, period=14):
        """Calcula el Average True Range (ATR)."""
        if len(closes) < period + 1:
            return None

        true_ranges = []
        for i in range(1, len(closes)):
            tr = max(
                highs[i] - lows[i],
                abs(highs[i] - closes[i - 1]),
                abs(lows[i] - closes[i - 1]),
            )
            true_ranges.append(tr)

        if len(true_ranges) < period:
            return None

        atr = np.mean(true_ranges[-period:])
        return atr

    def analyze(self, candles_data):
        """
        Analiza las velas y genera una senal de trading.

        Args:
            candles_data (list): Lista de diccionarios con datos de velas.
                Cada vela debe tener: open, close, high, low, volume

        Returns:
            dict: Resultado del analisis con:
                - direction: "CALL", "PUT" o None
                - confidence: Porcentaje de confianza (0-100)
                - indicators: Valores de indicadores
                - reasons: Lista de razones para la senal
        """
        if not candles_data or len(candles_data) < self.macd_slow + 10:
            logger.warning(
                "Datos insuficientes para analisis: %d velas",
                len(candles_data) if candles_data else 0,
            )
            return {
                "direction": None,
                "confidence": 0,
                "indicators": {},
                "reasons": ["Datos insuficientes"],
            }

        # Extraer arrays de precios
        closes = [c["close"] for c in candles_data]
        highs = [c["high"] for c in candles_data]
        lows = [c["low"] for c in candles_data]
        opens = [c["open"] for c in candles_data]

        current_price = closes[-1]

        # Calcular indicadores
        rsi = self.calculate_rsi(closes)
        ema_fast_val = self.calculate_ema(closes, self.ema_fast)
        ema_slow_val = self.calculate_ema(closes, self.ema_slow)
        bb_upper, bb_middle, bb_lower = self.calculate_bollinger_bands(closes)
        macd_val, macd_signal_val, macd_hist = self.calculate_macd(closes)
        stoch_k, stoch_d = self.calculate_stochastic(highs, lows, closes)
        atr = self.calculate_atr(highs, lows, closes)

        # Almacenar indicadores
        indicators = {
            "rsi": rsi,
            "ema_fast": ema_fast_val,
            "ema_slow": ema_slow_val,
            "bb_upper": bb_upper,
            "bb_middle": bb_middle,
            "bb_lower": bb_lower,
            "macd": macd_val,
            "macd_signal": macd_signal_val,
            "macd_histogram": macd_hist,
            "stoch_k": stoch_k,
            "stoch_d": stoch_d,
            "atr": atr,
            "price": current_price,
        }

        # Verificar que todos los indicadores se calcularon
        essential_indicators = [rsi, ema_fast_val, ema_slow_val, bb_upper, macd_val]
        if any(ind is None for ind in essential_indicators):
            return {
                "direction": None,
                "confidence": 0,
                "indicators": indicators,
                "reasons": ["Indicadores no disponibles"],
            }

        # Sistema de puntuacion para senales
        call_score = 0
        put_score = 0
        reasons_call = []
        reasons_put = []
        total_weight = 0

        # --- RSI (peso: 20) ---
        weight_rsi = 20
        total_weight += weight_rsi
        if rsi < config.RSI_OVERSOLD:
            call_score += weight_rsi
            reasons_call.append(f"RSI sobrevendido ({rsi:.1f})")
        elif rsi > config.RSI_OVERBOUGHT:
            put_score += weight_rsi
            reasons_put.append(f"RSI sobrecomprado ({rsi:.1f})")
        elif rsi < 45:
            call_score += weight_rsi * 0.3
            reasons_call.append(f"RSI bajo ({rsi:.1f})")
        elif rsi > 55:
            put_score += weight_rsi * 0.3
            reasons_put.append(f"RSI alto ({rsi:.1f})")

        # --- EMA Crossover (peso: 25) ---
        weight_ema = 25
        total_weight += weight_ema
        if ema_fast_val > ema_slow_val:
            ema_diff_pct = ((ema_fast_val - ema_slow_val) / ema_slow_val) * 100
            if ema_diff_pct > 0.01:
                call_score += weight_ema
                reasons_call.append(
                    f"EMA rapida > EMA lenta (diff: {ema_diff_pct:.4f}%)"
                )
            else:
                call_score += weight_ema * 0.5
                reasons_call.append("EMA cruce alcista debil")
        else:
            ema_diff_pct = ((ema_slow_val - ema_fast_val) / ema_fast_val) * 100
            if ema_diff_pct > 0.01:
                put_score += weight_ema
                reasons_put.append(
                    f"EMA lenta > EMA rapida (diff: {ema_diff_pct:.4f}%)"
                )
            else:
                put_score += weight_ema * 0.5
                reasons_put.append("EMA cruce bajista debil")

        # --- Bollinger Bands (peso: 20) ---
        weight_bb = 20
        total_weight += weight_bb
        if current_price <= bb_lower:
            call_score += weight_bb
            reasons_call.append("Precio en banda inferior de Bollinger")
        elif current_price >= bb_upper:
            put_score += weight_bb
            reasons_put.append("Precio en banda superior de Bollinger")
        elif current_price < bb_middle:
            call_score += weight_bb * 0.3
        else:
            put_score += weight_bb * 0.3

        # --- MACD (peso: 20) ---
        weight_macd = 20
        total_weight += weight_macd
        if macd_val is not None and macd_signal_val is not None:
            if macd_val > macd_signal_val:
                call_score += weight_macd
                reasons_call.append("MACD por encima de la senal")
            else:
                put_score += weight_macd
                reasons_put.append("MACD por debajo de la senal")

            # Divergencia del histograma
            if macd_hist is not None and macd_hist > 0:
                call_score += weight_macd * 0.2
            elif macd_hist is not None:
                put_score += weight_macd * 0.2

        # --- Stochastic (peso: 15) ---
        weight_stoch = 15
        total_weight += weight_stoch
        if stoch_k is not None and stoch_d is not None:
            if not np.isnan(stoch_k) and not np.isnan(stoch_d):
                if stoch_k < config.STOCH_OVERSOLD and stoch_d < config.STOCH_OVERSOLD:
                    call_score += weight_stoch
                    reasons_call.append(
                        f"Estocastico sobrevendido (K:{stoch_k:.1f}, D:{stoch_d:.1f})"
                    )
                elif (
                    stoch_k > config.STOCH_OVERBOUGHT
                    and stoch_d > config.STOCH_OVERBOUGHT
                ):
                    put_score += weight_stoch
                    reasons_put.append(
                        f"Estocastico sobrecomprado (K:{stoch_k:.1f}, D:{stoch_d:.1f})"
                    )
                elif stoch_k > stoch_d:
                    call_score += weight_stoch * 0.4
                else:
                    put_score += weight_stoch * 0.4

        # --- Patrones de velas (peso extra) ---
        if len(closes) >= 3:
            # Detectar tendencia reciente
            recent_trend = closes[-1] - closes[-3]
            if recent_trend > 0:
                call_score += 5
                reasons_call.append("Tendencia alcista reciente")
            elif recent_trend < 0:
                put_score += 5
                reasons_put.append("Tendencia bajista reciente")
            total_weight += 5

            # Detectar vela envolvente
            prev_body = closes[-2] - opens[-2]
            curr_body = closes[-1] - opens[-1]
            if prev_body < 0 and curr_body > 0 and abs(curr_body) > abs(prev_body):
                call_score += 5
                reasons_call.append("Patron envolvente alcista")
            elif prev_body > 0 and curr_body < 0 and abs(curr_body) > abs(prev_body):
                put_score += 5
                reasons_put.append("Patron envolvente bajista")
            total_weight += 5

        # Calcular confianza y direccion
        if total_weight == 0:
            return {
                "direction": None,
                "confidence": 0,
                "indicators": indicators,
                "reasons": ["Sin datos suficientes"],
            }

        call_confidence = (call_score / total_weight) * 100
        put_confidence = (put_score / total_weight) * 100

        if call_confidence > put_confidence:
            direction = "CALL"
            confidence = call_confidence
            reasons = reasons_call
        elif put_confidence > call_confidence:
            direction = "PUT"
            confidence = put_confidence
            reasons = reasons_put
        else:
            direction = None
            confidence = 0
            reasons = ["Senal neutral - sin direccion clara"]

        logger.info(
            "Analisis completado: %s con %.1f%% confianza",
            direction or "NEUTRAL",
            confidence,
        )

        return {
            "direction": direction,
            "confidence": confidence,
            "indicators": indicators,
            "reasons": reasons,
        }
