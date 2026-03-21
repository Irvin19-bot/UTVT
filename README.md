# 🤖 Scalping Trading Bot

Bot de trading automatizado con estrategia **scalping** que analiza mercados financieros usando indicadores técnicos y envía alertas de operación a un grupo de Telegram.

## 📊 Indicadores Técnicos

El bot utiliza 5 indicadores para generar señales de compra/venta:

| Indicador | Compra | Venta |
|-----------|--------|-------|
| **RSI** (14) | RSI ≤ 30 (sobreventa) | RSI ≥ 70 (sobrecompra) |
| **MACD** (12/26/9) | Cruce alcista | Cruce bajista |
| **Bollinger Bands** (20, 2σ) | Precio en banda inferior | Precio en banda superior |
| **EMA** (9/21) | EMA rápida > EMA lenta | EMA rápida < EMA lenta |
| **Volumen** | Volumen > 1.5x promedio | Volumen > 1.5x promedio |

Se requieren **al menos 3 de 5** indicadores de acuerdo para generar una alerta.

## 🚀 Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/Irvin19-bot/UTVT.git
cd UTVT
```

### 2. Crear entorno virtual

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

```bash
cp .env.example .env
```

Edita el archivo `.env` con tus credenciales:

```env
TELEGRAM_BOT_TOKEN=tu_token_aqui
TELEGRAM_CHAT_ID=tu_chat_id_aqui
TICKERS=AAPL,MSFT,GOOGL,AMZN,TSLA,META,NVDA,BTC-USD,ETH-USD
```

## 🔑 Configuración de Telegram

### Crear un Bot

1. Abre Telegram y busca **@BotFather**
2. Envía `/newbot` y sigue las instrucciones
3. Copia el **token** que te proporcione

### Obtener el Chat ID del grupo

1. Agrega el bot a tu grupo de Telegram
2. Agrega **@userinfobot** al grupo (o envía un mensaje al grupo y revisa `https://api.telegram.org/bot<TOKEN>/getUpdates`)
3. El Chat ID del grupo generalmente empieza con `-100...`

## 💻 Uso

### Modo continuo (recomendado)

Ejecuta el bot con análisis programado cada hora:

```bash
python main.py
```

### Ejecución única

Ejecuta el análisis una sola vez y termina:

```bash
python main.py --once
```

## 📁 Estructura del Proyecto

```
UTVT/
├── main.py                      # Punto de entrada
├── requirements.txt             # Dependencias
├── .env.example                 # Plantilla de configuración
├── bot/
│   ├── __init__.py
│   ├── config.py                # Configuración y parámetros
│   ├── analyzer.py              # Orquestador de análisis
│   ├── strategies/
│   │   ├── __init__.py
│   │   └── scalping.py          # Estrategia scalping
│   └── services/
│       ├── __init__.py
│       ├── market_data.py       # Datos de mercado (yfinance)
│       └── telegram_service.py  # Servicio de alertas Telegram
```

## ⚙️ Parámetros Configurables

Los parámetros de la estrategia se pueden ajustar en `bot/config.py`:

- **RSI**: período, niveles de sobrecompra/sobreventa
- **MACD**: períodos rápido, lento y señal
- **Bollinger Bands**: período y desviaciones estándar
- **EMA**: períodos rápido y lento
- **Volumen**: multiplicador mínimo vs promedio
- **Señales mínimas**: cantidad de indicadores requeridos para generar alerta

## ⚠️ Disclaimer

Este bot es una herramienta de análisis técnico y **no constituye asesoramiento financiero**. El trading conlleva riesgos significativos. Opera bajo tu propio riesgo y nunca inviertas más de lo que puedas permitirte perder.
