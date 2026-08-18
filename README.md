# Fintrova

Agente AI financiero que responde preguntas de mercado en lenguaje natural
("¿cómo está el EUR/USD hoy?", "¿hay señal de compra en Apple?") con datos
reales, análisis técnico y alertas.

Proyecto para el **DevNetwork [API + Cloud + AI] Hackathon 2026**
(17 agosto – 3 septiembre 2026).

## Stack

- **Agente/LLM:** Claude API (Anthropic) con tool calling
- **Datos de mercado:** Alpha Vantage
- **Noticias:** SerpApi
- **Frontend:** Streamlit
- **Deploy:** OCI Free Tier

## Estructura

```
fintrova/
├── app.py              # Interfaz Streamlit
├── agent.py             # Lógica del agente Claude
├── tools/
│   ├── market_data.py   # Conexión Alpha Vantage
│   ├── indicators.py    # RSI, MACD, medias
│   └── alerts.py        # Generación de alertas
├── .env                 # API keys (no versionado)
├── requirements.txt
└── README.md
```

## Setup

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env  # completar API keys
```
