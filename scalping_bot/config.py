"""
Configuración del bot de scalping.
Se recomienda usar variables de entorno para los datos sensibles.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# =====================================================
# Configuración de IQ Option
# =====================================================
IQ_EMAIL = os.getenv("IQ_OPTION_EMAIL", "")
IQ_PASSWORD = os.getenv("IQ_OPTION_PASSWORD", "")
# Modo: "PRACTICE" para cuenta demo, "REAL" para cuenta real
IQ_ACCOUNT_TYPE = os.getenv("IQ_ACCOUNT_TYPE", "PRACTICE")

# =====================================================
# Configuración de Telegram
# =====================================================
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_GROUP_ID = int(os.getenv("TELEGRAM_GROUP_ID", "0"))

# =====================================================
# Configuración de la estrategia de Scalping
# =====================================================
# Activos a monitorear (pares de divisas y criptos populares)
ASSETS = [
    "EURUSD",
    "GBPUSD",
    "USDJPY",
    "AUDUSD",
    "EURGBP",
    "USDCHF",
    "EURJPY",
    "GBPJPY",
]

# Temporalidad de las velas (en segundos)
# 60 = 1 minuto (ideal para scalping)
CANDLE_PERIOD = 60

# Cantidad de velas históricas para análisis
CANDLE_COUNT = 100

# Intervalo de análisis (en segundos)
ANALYSIS_INTERVAL = 5

# =====================================================
# Parámetros de indicadores técnicos
# =====================================================
# RSI (Relative Strength Index)
RSI_PERIOD = 14
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30

# EMA (Exponential Moving Average)
EMA_FAST = 9
EMA_SLOW = 21

# Bollinger Bands
BB_PERIOD = 20
BB_STD_DEV = 2

# MACD
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9

# =====================================================
# Configuración de gestión de riesgo
# =====================================================
# Porcentaje de confianza mínimo para enviar señal (0-100)
MIN_CONFIDENCE = 65

# Tiempo de expiración de la operación en minutos
EXPIRATION_TIME = 1

# Monto de operación por defecto
DEFAULT_AMOUNT = 1.0
