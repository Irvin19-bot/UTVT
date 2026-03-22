# 🤖 Scalping Trading Bot - IQ Option + Telegram

Bot automatizado de trading con estrategia de scalping que se conecta al broker **IQ Option**, analiza el mercado en tiempo real y envía señales de compra/venta a un grupo de **Telegram**.

## 📋 Características

- **Conexión en tiempo real** con IQ Option para obtener datos de mercado
- **Estrategia de Scalping Multi-Indicador**:
  - RSI (Relative Strength Index)
  - EMA (Exponential Moving Average) - Cruce rápido/lento
  - Bollinger Bands
  - MACD (Moving Average Convergence Divergence)
  - Análisis de volumen
  - Stochastic RSI para confirmación
- **Señales automáticas** enviadas a Telegram con análisis detallado
- **Gestión de riesgo** con Stop Loss y Take Profit basados en ATR
- **Sistema de cooldown** para evitar señales duplicadas
- **Soporte para cuenta demo y real**

## 🚀 Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/Irvin19-bot/UTVT.git
cd UTVT
```

### 2. Crear entorno virtual (recomendado)

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# o
venv\Scripts\activate     # Windows
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

Copia el archivo de ejemplo y completa tus datos:

```bash
cp .env.example .env
```

Edita el archivo `.env` con tus credenciales:

```env
IQ_OPTION_EMAIL=tu_email@ejemplo.com
IQ_OPTION_PASSWORD=tu_contraseña
IQ_ACCOUNT_TYPE=PRACTICE
TELEGRAM_BOT_TOKEN=tu_token_de_telegram
TELEGRAM_GROUP_ID=tu_id_de_grupo
```

## ▶️ Uso

### Ejecutar el bot

```bash
python -m scalping_bot.bot
```

### Variables de entorno alternativas

También puedes configurar las variables directamente:

```bash
export IQ_OPTION_EMAIL='tu_email@ejemplo.com'
export IQ_OPTION_PASSWORD='tu_contraseña'
python -m scalping_bot.bot
```

## 📊 Estrategia de Scalping

El bot utiliza una combinación ponderada de indicadores técnicos:

| Indicador | Peso | Descripción |
|-----------|------|-------------|
| RSI | 25% | Detecta condiciones de sobrecompra/sobreventa |
| EMA (9/21) | 25% | Detecta cruces y tendencias |
| Bollinger Bands | 20% | Detecta niveles de precio extremos |
| MACD | 20% | Confirma momentum y tendencia |
| Volumen | 10% | Confirma la fuerza del movimiento |

### Señales

- **COMPRA (CALL)**: Cuando los indicadores combinados muestran una tendencia alcista con confianza >= 65%
- **VENTA (PUT)**: Cuando los indicadores combinados muestran una tendencia bajista con confianza >= 65%

### Activos monitoreados por defecto

- EURUSD, GBPUSD, USDJPY, AUDUSD
- EURGBP, USDCHF, EURJPY, GBPJPY

## 📱 Ejemplo de señal en Telegram

```
🟢 SEÑAL DE COMPRA (CALL) 🟢
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 Activo: EURUSD
💰 Precio actual: 1.08542
📈 Dirección: ⬆️ ALCISTA
🎯 Confianza: 78.5%
🟩🟩🟩🟩🟩🟩🟩🟩⬜⬜

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 ANÁLISIS TÉCNICO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📉 RSI (28.5): Sobreventa
📊 EMA: CRUCE ALCISTA
📏 Bollinger: TOCA BANDA INFERIOR
📐 MACD: MOMENTUM ALCISTA
📊 Volumen: VOLUMEN ALTO

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 NIVELES CLAVE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🟢 Soporte: 1.08400
🔴 Resistencia: 1.08700
🛑 Stop Loss: 1.08392
✅ Take Profit: 1.08742
```

## ⚙️ Configuración avanzada

Puedes modificar los parámetros en `scalping_bot/config.py`:

- **Indicadores**: Períodos de RSI, EMA, Bollinger Bands, MACD
- **Confianza mínima**: Porcentaje mínimo para enviar señal (default: 65%)
- **Activos**: Lista de pares a monitorear
- **Temporalidad**: Período de velas (default: 1 minuto)
- **Intervalo**: Frecuencia de análisis (default: 5 segundos)

## ⚠️ Disclaimer

Este bot es una herramienta educativa y de asistencia. **No garantiza ganancias**. El trading conlleva riesgos significativos y puedes perder tu capital. Úsalo bajo tu propia responsabilidad. Se recomienda:

- Comenzar con cuenta **PRACTICE** (demo)
- No invertir dinero que no puedas permitirte perder
- Verificar las señales manualmente antes de operar
- Usar gestión de riesgo adecuada

## 📄 Licencia

Este proyecto es de uso educativo.
