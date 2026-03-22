# Bot de Scalping - IQ Option

Bot de trading automatizado con estrategia de scalping para IQ Option que envia senales de compra/venta a un grupo de Telegram.

## Caracteristicas

- **Conexion en tiempo real** con IQ Option via API
- **Analisis tecnico multi-indicador:**
  - RSI (Relative Strength Index)
  - Bollinger Bands
  - EMA (Exponential Moving Average) - Cruce rapido/lento
  - MACD (Moving Average Convergence Divergence)
  - Oscilador Estocastico
  - ATR (Average True Range)
  - Patrones de velas (envolventes)
- **Operaciones de 5 minutos** (scalping)
- **Senales automaticas** enviadas a Telegram con nivel de confianza
- **Modo demo y real** - practica sin riesgo
- **Auto-trade opcional** - ejecuta operaciones automaticamente
- **Control de riesgo** - limite de operaciones por hora

## Requisitos

- Python 3.8+
- Cuenta de IQ Option
- Bot de Telegram y grupo configurado

## Instalacion

```bash
# Clonar el repositorio
git clone https://github.com/Irvin19-bot/UTVT.git
cd UTVT

# Instalar dependencias
pip install -r requirements.txt

# Instalar la API de IQ Option
pip install -U git+https://github.com/iqoptionapi/iqoptionapi.git
```

## Configuracion

### Variables de Entorno (Recomendado)

```bash
export IQ_EMAIL="tu_correo@ejemplo.com"
export IQ_PASSWORD="tu_contrasenya"
export TELEGRAM_TOKEN="tu_token_de_bot"
export TELEGRAM_CHAT_ID="tu_chat_id"
```

### Archivo config.py

Tambien puedes editar directamente el archivo `config.py` para ajustar:

- Credenciales de IQ Option y Telegram
- Parametros de indicadores tecnicos (RSI, BB, EMA, MACD, etc.)
- Pares de divisas a monitorear
- Tiempo de expiracion de operaciones
- Monto de inversion
- Confianza minima para senales
- Limite de operaciones por hora

## Uso

### Solo Senales (Recomendado para empezar)

```bash
python bot.py
```

El bot analizara el mercado y enviara senales de compra/venta al grupo de Telegram sin ejecutar operaciones.

### Auto-Trade (Modo Demo)

```bash
python bot.py --auto-trade --demo
```

Ejecuta operaciones automaticamente en la cuenta demo.

### Auto-Trade (Modo Real) - PRECAUCION

```bash
python bot.py --auto-trade --real
```

> **ADVERTENCIA:** Este modo ejecuta operaciones con dinero real. Usalo bajo tu propia responsabilidad.

## Estructura del Proyecto

```
UTVT/
├── bot.py                 # Bot principal
├── config.py              # Configuracion
├── iq_connection.py       # Conexion con IQ Option
├── technical_analysis.py  # Analisis tecnico
├── telegram_sender.py     # Envio de senales a Telegram
├── requirements.txt       # Dependencias
└── README.md              # Documentacion
```

## Estrategia de Scalping

El bot utiliza un sistema de puntuacion multi-indicador:

| Indicador | Peso | Senal CALL | Senal PUT |
|-----------|------|------------|-----------|
| RSI | 20% | RSI < 30 (sobrevendido) | RSI > 70 (sobrecomprado) |
| EMA | 25% | EMA rapida > EMA lenta | EMA lenta > EMA rapida |
| Bollinger | 20% | Precio en banda inferior | Precio en banda superior |
| MACD | 20% | MACD > Senal | MACD < Senal |
| Estocastico | 15% | %K y %D < 20 | %K y %D > 80 |

Se generan senales adicionales por patrones de velas y tendencia reciente.

## Disclaimer

Este bot es una herramienta de analisis tecnico. El trading de opciones binarias conlleva riesgos significativos de perdida. Las senales generadas no garantizan ganancias. Usa esta herramienta bajo tu propia responsabilidad y nunca inviertas dinero que no puedas permitirte perder.
