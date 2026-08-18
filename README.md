<div align="center">

<img src="assets/logo.png" alt="Fintrova" width="140"/>

# 💎 Fintrova

**Tu analista financiero personal, en lenguaje natural.**

Un agente de IA que responde preguntas de mercado — acciones, cripto, forex, índices y materias primas — con datos reales, análisis técnico y señales de compra/venta.

Construido para el **[DevNetwork API + Cloud + AI Hackathon 2026](https://api-cloud-ai-hackathon-2026.devpost.com/)** 🏆

</div>

---

## 🧠 ¿Qué hace?

Le preguntas en español o inglés, como le preguntarías a un analista:

> *"¿Cómo está el EUR/USD hoy?"*
> *"¿Hay señal de compra en Apple?"*
> *"Dame el RSI de Bitcoin y las noticias recientes"*

Fintrova entiende la pregunta, decide qué datos necesita, los busca en tiempo real y responde con el análisis — sin que tengas que saber qué API o qué indicador usar.

## ✨ Features

- 💬 **Chat en lenguaje natural** con tool calling real (Claude decide qué herramientas llamar)
- 🧵 **Memoria de conversación** — persiste en SQLite, sobrevive reinicios del servidor, y el agente resuelve seguimientos ("¿y su RSI?") con contexto real
- 📈 **Precio e historial** de acciones, ETFs, índices, forex, cripto y materias primas
- 📊 **Indicadores técnicos** — RSI, MACD, medias móviles (SMA20/SMA50)
- 🚨 **Alertas de señales** — sobrecompra/sobreventa, momentum, tendencia
- 📉 **Backtesting de señales** — mide qué retorno tuvo el precio históricamente después de cada señal de RSI, con tasa de acierto, cacheado 24h
- 📰 **Noticias financieras** en tiempo real por activo, con **síntesis de sentimiento** (no solo titulares)
- 🖼️ **Lectura de gráficos con visión** — sube un screenshot de un chart y Claude lo analiza directamente
- 🛡️ **Manejo de errores real** — rate limits, símbolos inválidos y fallos de red se explican en lenguaje natural, nunca un crash
- 🎨 **Identidad visual propia** — el avatar del agente literalmente "escala" la línea de precios mientras piensa

## 🪙 Instrumentos soportados

| Tipo | Ejemplos |
|---|---|
| Acciones / ETFs | `AAPL`, `TSLA`, `SPY` |
| Índices | S&P 500, Nasdaq, Dow (vía su ETF de referencia) |
| Forex | `EUR/USD`, `GBP/JPY` |
| Cripto | `BTC/USD`, `ETH/USD` |
| Materias primas | petróleo/WTI, brent, gas natural, cobre, trigo, maíz, algodón, azúcar, café |

## 🛠️ Stack

| Capa | Tecnología |
|---|---|
| Agente / LLM | [Claude API](https://www.anthropic.com/) (Anthropic) — tool calling |
| Datos de mercado | [Alpha Vantage](https://www.alphavantage.co/) |
| Noticias | [SerpApi](https://serpapi.com/) — `google_finance` engine |
| Frontend | [Streamlit](https://streamlit.io/) |
| Deploy | Oracle Cloud Infrastructure — Always Free Tier |

## 📁 Estructura

```
fintrova/
├── app.py                       # Interfaz Streamlit
├── agent.py                     # Agente Claude + tool calling
├── tools/
│   ├── market_data.py           # Precio, historial y noticias (Alpha Vantage + SerpApi)
│   ├── indicators.py            # RSI, MACD, medias móviles
│   └── alerts.py                # Señales de compra/venta
├── assets/                      # Marca (logo estático + avatar animado)
├── scripts/
│   └── generate_brand_assets.py # Regenera los assets de marca
├── .env.example                 # Plantilla de variables de entorno
├── requirements.txt
└── README.md
```

## 🚀 Setup

```bash
git clone https://github.com/Liuberth33/fintrova.git
cd fintrova
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env  # completar con tus API keys
```

Necesitas tres API keys gratuitas: [Anthropic Console](https://console.anthropic.com/), [Alpha Vantage](https://www.alphavantage.co/support/#api-key) y [SerpApi](https://serpapi.com/manage-api-key).

## ▶️ Correr la app

```bash
streamlit run app.py --server.port 8502
```

> El puerto se fija en `8502` para evitar chocar con otros proyectos Streamlit locales que usen el puerto 8501 por defecto.

## 🏆 Sobre el hackathon

Fintrova participa en el **DevNetwork [API + Cloud + AI] Hackathon 2026** (17 ago – 3 sep 2026), aplicando al challenge de **SerpApi** por su integración de datos en tiempo real para noticias financieras.

---

<div align="center">

<img src="assets/logo.png" alt="Fintrova" width="140"/>

# 💎 Fintrova

**Your personal financial analyst, in natural language.**

An AI agent that answers market questions — stocks, crypto, forex, indices, and commodities — with real data, technical analysis, and buy/sell signals.

Built for the **[DevNetwork API + Cloud + AI Hackathon 2026](https://api-cloud-ai-hackathon-2026.devpost.com/)** 🏆

</div>

---

## 🧠 What it does

Ask it like you'd ask an analyst, in Spanish or English:

> *"How's EUR/USD doing today?"*
> *"Is there a buy signal on Apple?"*
> *"Give me Bitcoin's RSI and recent news"*

Fintrova understands the question, figures out what data it needs, fetches it in real time, and answers with the analysis — no need to know which API or indicator to use.

## ✨ Features

- 💬 **Natural-language chat** with real tool calling (Claude decides which tools to call)
- 🧵 **Conversation memory** — persists in SQLite, survives server restarts, and the agent resolves follow-ups ("what about its RSI?") with real context
- 📈 **Price and history** for stocks, ETFs, indices, forex, crypto, and commodities
- 📊 **Technical indicators** — RSI, MACD, moving averages (SMA20/SMA50)
- 🚨 **Signal alerts** — overbought/oversold, momentum, trend
- 📉 **Signal backtesting** — measures how price historically performed after each RSI signal, with hit rate, cached 24h
- 📰 **Real-time financial news** per asset, with **sentiment synthesis** (not just headlines)
- 🖼️ **Chart reading via vision** — upload a chart screenshot and Claude analyzes it directly
- 🛡️ **Real error handling** — rate limits, invalid symbols, and network failures get explained in plain language, never a crash
- 🎨 **Its own visual identity** — the agent's avatar literally "climbs" the price line while it thinks

## 🪙 Supported instruments

| Type | Examples |
|---|---|
| Stocks / ETFs | `AAPL`, `TSLA`, `SPY` |
| Indices | S&P 500, Nasdaq, Dow (via their tracking ETF) |
| Forex | `EUR/USD`, `GBP/JPY` |
| Crypto | `BTC/USD`, `ETH/USD` |
| Commodities | oil/WTI, brent, natural gas, copper, wheat, corn, cotton, sugar, coffee |

## 🛠️ Stack

| Layer | Technology |
|---|---|
| Agent / LLM | [Claude API](https://www.anthropic.com/) (Anthropic) — tool calling |
| Market data | [Alpha Vantage](https://www.alphavantage.co/) |
| News | [SerpApi](https://serpapi.com/) — `google_finance` engine |
| Frontend | [Streamlit](https://streamlit.io/) |
| Deploy | Oracle Cloud Infrastructure — Always Free Tier |

## 🚀 Setup

```bash
git clone https://github.com/Liuberth33/fintrova.git
cd fintrova
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env  # fill in your API keys
```

You'll need three free API keys: [Anthropic Console](https://console.anthropic.com/), [Alpha Vantage](https://www.alphavantage.co/support/#api-key), and [SerpApi](https://serpapi.com/manage-api-key).

## ▶️ Run the app

```bash
streamlit run app.py --server.port 8502
```

> The port is pinned to `8502` to avoid clashing with other local Streamlit projects using the default 8501.

## 🏆 About the hackathon

Fintrova is an entry for the **DevNetwork [API + Cloud + AI] Hackathon 2026** (Aug 17 – Sep 3, 2026), applying to the **SerpApi** challenge for its real-time financial news integration.
