import json
import os

import anthropic
from dotenv import load_dotenv

from tools.alerts import generate_alert
from tools.indicators import calculate_indicators
from tools.market_data import get_history, get_news, get_price

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

MODEL = "claude-sonnet-5"

SYSTEM_PROMPT = (
    "Eres Fintrova, un analista financiero personal. Respondes preguntas de "
    "mercado en lenguaje natural usando datos reales de precios, noticias e "
    "indicadores técnicos. Sé directo y concreto: da el dato, el análisis "
    "técnico si aplica, y evita relleno. Nunca des asesoría financiera "
    "personalizada de inversión, solo información y análisis técnico."
)

TOOLS = [
    {
        "name": "get_price",
        "description": (
            "Precio actual de un activo: acción, ETF, índice, forex, "
            "criptomoneda o materia prima."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": (
                        "Símbolo del activo. Acepta: tickers de acciones/ETFs (AAPL, SPY), "
                        "índices por su nombre común (S&P 500, Nasdaq, Dow — se resuelven vía "
                        "su ETF de referencia), pares de forex (EUR/USD), criptomonedas en "
                        "formato par (BTC/USD, ETH/USD), y materias primas por nombre común "
                        "(petróleo/WTI, brent, gas natural, cobre, trigo, maíz, algodón, "
                        "azúcar, café). No soporta metales preciosos (oro, plata) — ninguna "
                        "fuente de datos disponible los cubre."
                    ),
                },
            },
            "required": ["symbol"],
        },
    },
    {
        "name": "get_history",
        "description": (
            "Historial de precios de los últimos N días/períodos para acciones, ETFs, "
            "índices, forex, cripto o materias primas."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": (
                        "Símbolo del activo. Acepta: tickers de acciones/ETFs (AAPL, SPY), "
                        "índices por su nombre común (S&P 500, Nasdaq, Dow — se resuelven vía "
                        "su ETF de referencia), pares de forex (EUR/USD), criptomonedas en "
                        "formato par (BTC/USD, ETH/USD), y materias primas por nombre común "
                        "(petróleo/WTI, brent, gas natural, cobre, trigo, maíz, algodón, "
                        "azúcar, café). No soporta metales preciosos (oro, plata) — ninguna "
                        "fuente de datos disponible los cubre."
                    ),
                },
                "days": {
                    "type": "integer",
                    "description": "Número de días de historial a devolver",
                },
            },
            "required": ["symbol"],
        },
    },
    {
        "name": "get_news",
        "description": (
            "Noticias financieras recientes relacionadas a un activo. Mejor cobertura "
            "en acciones, índices, forex y cripto; materias primas suelen tener poco "
            "o ningún resultado."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": (
                        "Símbolo del activo. Acepta: tickers de acciones/ETFs (AAPL, SPY), "
                        "índices por su nombre común (S&P 500, Nasdaq, Dow — se resuelven vía "
                        "su ETF de referencia), pares de forex (EUR/USD), criptomonedas en "
                        "formato par (BTC/USD, ETH/USD), y materias primas por nombre común "
                        "(petróleo/WTI, brent, gas natural, cobre, trigo, maíz, algodón, "
                        "azúcar, café). No soporta metales preciosos (oro, plata) — ninguna "
                        "fuente de datos disponible los cubre."
                    ),
                },
                "limit": {
                    "type": "integer",
                    "description": "Número máximo de noticias a devolver",
                },
            },
            "required": ["symbol"],
        },
    },
    {
        "name": "get_indicators",
        "description": (
            "Indicadores técnicos (RSI, MACD, medias móviles SMA20/SMA50) calculados "
            "sobre el historial reciente de cualquier activo soportado (acciones, "
            "índices, forex, cripto, materias primas)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": (
                        "Símbolo del activo. Acepta: tickers de acciones/ETFs (AAPL, SPY), "
                        "índices por su nombre común (S&P 500, Nasdaq, Dow — se resuelven vía "
                        "su ETF de referencia), pares de forex (EUR/USD), criptomonedas en "
                        "formato par (BTC/USD, ETH/USD), y materias primas por nombre común "
                        "(petróleo/WTI, brent, gas natural, cobre, trigo, maíz, algodón, "
                        "azúcar, café). No soporta metales preciosos (oro, plata) — ninguna "
                        "fuente de datos disponible los cubre."
                    ),
                },
                "days": {
                    "type": "integer",
                    "description": "Días de historial a usar para el cálculo (mínimo 60 recomendado para RSI/MACD confiables)",
                },
            },
            "required": ["symbol"],
        },
    },
    {
        "name": "get_alerts",
        "description": (
            "Detecta señales técnicas de compra/venta (sobrecompra/sobreventa RSI, "
            "momentum MACD, tendencia por medias móviles) para cualquier activo "
            "soportado (acciones, índices, forex, cripto, materias primas)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": (
                        "Símbolo del activo. Acepta: tickers de acciones/ETFs (AAPL, SPY), "
                        "índices por su nombre común (S&P 500, Nasdaq, Dow — se resuelven vía "
                        "su ETF de referencia), pares de forex (EUR/USD), criptomonedas en "
                        "formato par (BTC/USD, ETH/USD), y materias primas por nombre común "
                        "(petróleo/WTI, brent, gas natural, cobre, trigo, maíz, algodón, "
                        "azúcar, café). No soporta metales preciosos (oro, plata) — ninguna "
                        "fuente de datos disponible los cubre."
                    ),
                },
                "days": {
                    "type": "integer",
                    "description": "Días de historial a usar para el cálculo",
                },
            },
            "required": ["symbol"],
        },
    },
]


def _get_indicators(symbol: str, days: int = 60) -> dict:
    history = get_history(symbol, days=days)
    return calculate_indicators(history)


def _get_alerts(symbol: str, days: int = 60) -> list[dict]:
    return generate_alert(_get_indicators(symbol, days=days))


TOOL_FUNCTIONS = {
    "get_price": lambda symbol: get_price(symbol),
    "get_history": lambda symbol, days=30: get_history(symbol, days=days),
    "get_news": lambda symbol, limit=5: get_news(symbol, limit=limit),
    "get_indicators": _get_indicators,
    "get_alerts": _get_alerts,
}


def _execute_tool(name: str, tool_input: dict):
    return TOOL_FUNCTIONS[name](**tool_input)


def _friendly_error_message(error: Exception) -> str:
    if isinstance(error, anthropic.APIStatusError):
        if error.status_code == 400 and "credit balance" in str(error).lower():
            return (
                "No pude completar la consulta: tu cuenta de Anthropic no tiene crédito "
                "suficiente. Agrega crédito en console.anthropic.com → Plans & Billing e "
                "intenta de nuevo."
            )
        if error.status_code == 429:
            return "Se alcanzó el límite de solicitudes a Claude. Espera un momento e intenta de nuevo."
        if error.status_code == 401:
            return "La API key de Anthropic no es válida. Revisa ANTHROPIC_API_KEY en tu .env."
        return f"La API de Claude devolvió un error ({error.status_code}): {error.message}"
    if isinstance(error, anthropic.APIConnectionError):
        return "No pude conectarme a la API de Claude. Revisa tu conexión a internet."
    return f"Ocurrió un error inesperado: {error}"


def ask(question: str) -> dict:
    """Envía una pregunta al agente y devuelve {"text": ..., "news": [...]},
    resolviendo internamente cualquier llamada a tools que Claude decida
    hacer. `news` trae los artículos que el agente haya consultado con
    get_news durante la conversación, para mostrarlos como tarjetas en la UI
    en vez de solo texto plano."""
    messages = [{"role": "user", "content": question}]
    news: list[dict] = []

    while True:
        try:
            response = client.messages.create(
                model=MODEL,
                max_tokens=1024,
                system=SYSTEM_PROMPT,
                tools=TOOLS,
                messages=messages,
            )
        except anthropic.APIError as error:
            return {"text": _friendly_error_message(error), "news": news}

        if response.stop_reason != "tool_use":
            text = "".join(block.text for block in response.content if block.type == "text")
            return {"text": text, "news": news}

        messages.append({"role": "assistant", "content": response.content})

        tool_results = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            try:
                result = _execute_tool(block.name, block.input)
                if block.name == "get_news":
                    news.extend(result)
                content = json.dumps(result, ensure_ascii=False)
            except Exception as error:
                content = json.dumps({"error": str(error)})
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": content,
            })

        messages.append({"role": "user", "content": tool_results})
