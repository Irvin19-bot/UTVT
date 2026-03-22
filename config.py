"""
Configuracion del Bot de Scalping para IQ Option
=================================================
IMPORTANTE: Para uso en produccion, configura las credenciales
como variables de entorno en lugar de valores directos.

Variables de entorno soportadas:
    IQ_EMAIL        - Correo de IQ Option
    IQ_PASSWORD     - Contrasena de IQ Option
    TELEGRAM_TOKEN  - Token del bot de Telegram
    TELEGRAM_CHAT_ID - ID del grupo de Telegram
"""

import os

# =============================================
# Configuracion de IQ Option
# =============================================
IQ_EMAIL = os.getenv("IQ_EMAIL", "al221810725@gmail.com")
IQ_PASSWORD = os.getenv("IQ_PASSWORD", "Escandalo86$")
ACCOUNT_TYPE = "PRACTICE"  # "PRACTICE" para demo, "REAL" para cuenta real

# =============================================
# Configuracion de Telegram
# =============================================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "8327269641:AAEuJuwvpsRsYwZHwTsVT0ZhKA4sWzAeRsw")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "-5222798489")

# =============================================
# Configuracion de Trading (Scalping)
# =============================================
EXPIRATION_TIME = 5  # Duracion de operacion en minutos
INVESTMENT_AMOUNT = 1  # Monto de inversion por operacion (USD)
MARTINGALE_ENABLED = False  # Habilitar martingala
MARTINGALE_MULTIPLIER = 2.2  # Multiplicador de martingala
MAX_MARTINGALE_STEPS = 3  # Pasos maximos de martingala

# =============================================
# Configuracion de Analisis Tecnico
# =============================================
# RSI
RSI_PERIOD = 14
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30

# Bollinger Bands
BB_PERIOD = 20
BB_STD_DEV = 2

# EMA
EMA_FAST = 9
EMA_SLOW = 21

# MACD
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9

# Stochastic
STOCH_K = 14
STOCH_D = 3
STOCH_OVERBOUGHT = 80
STOCH_OVERSOLD = 20

# =============================================
# Pares de divisas a monitorear
# =============================================
ASSETS = [
    "EURUSD",
    "GBPUSD",
    "USDJPY",
    "EURJPY",
    "GBPJPY",
    "AUDUSD",
    "USDCAD",
    "EURGBP",
]

# =============================================
# Configuracion del Bot
# =============================================
CANDLE_PERIOD = 60  # Periodo de velas en segundos (1 minuto)
NUM_CANDLES = 100  # Cantidad de velas historicas a analizar
MIN_CONFIDENCE = 70  # Confianza minima para enviar senal (%)
ANALYSIS_INTERVAL = 30  # Intervalo de analisis en segundos
MAX_OPERATIONS_PER_HOUR = 10  # Maximo de operaciones por hora
