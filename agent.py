import json
import os

import anthropic
from dotenv import load_dotenv
from langdetect import LangDetectException, detect

from tools.alerts import generate_alert
from tools.backtest import backtest_rsi_signal
from tools.indicators import calculate_indicators
from tools.market_data import get_history, get_news, get_price

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

MODEL = "claude-sonnet-5"

SYSTEM_PROMPT = (
    "LANGUAGE RULE (top priority, overrides everything below): detect the "
    "language of the user's most recent message and reply ENTIRELY in that "
    "language. If their message is in English, your whole answer must be in "
    "English, with zero Spanish words — even though the rest of this system "
    "prompt, the tool names, and the tool descriptions are written in "
    "Spanish. That is just internal configuration and must NOT leak into "
    "your response language. If their message is in Spanish, answer "
    "entirely in Spanish. Never mix both languages in one response.\n\n"
    "Eres Fintrova, un analista financiero personal. Respondes preguntas de "
    "mercado en lenguaje natural usando datos reales de precios, noticias e "
    "indicadores técnicos. Sé directo y concreto: da el dato, el análisis "
    "técnico si aplica, y evita relleno. Nunca des asesoría financiera "
    "personalizada de inversión, solo información y análisis técnico.\n\n"
    "Cuando uses get_news, no te limites a listar los titulares: sintetiza "
    "el sentimiento neto que reflejan (positivo, negativo, neutral o mixto) "
    "y explica en una frase por qué — qué noticias pesan más y en qué "
    "dirección. El usuario quiere una lectura, no una lista cruda.\n\n"
    "Si el usuario adjunta una imagen de un gráfico de precios, analízala "
    "directamente con tu visión: identifica patrones, soportes/resistencias "
    "visibles, tendencia y cualquier indicador que se vea en el chart. Si "
    "el activo del gráfico es identificable, puedes complementar con datos "
    "reales llamando a las tools disponibles.\n\n"
    "Responde siempre en el mismo idioma en que está escrita la pregunta del "
    "usuario (español o inglés), sin importar en qué idioma esté este "
    "prompt de sistema. Si el usuario cambia de idioma a mitad de la "
    "conversación, sigue el idioma del mensaje más reciente."
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
            "Noticias financieras recientes relacionadas a un activo. Úsala para poder "
            "sintetizar el sentimiento de mercado del activo (positivo/negativo/mixto), "
            "no solo para listar titulares. Mejor cobertura en acciones, índices, forex "
            "y cripto; materias primas suelen tener poco o ningún resultado."
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
    {
        "name": "backtest_rsi_signal",
        "description": (
            "Backtest de la señal de RSI(14) sobrecompra/sobreventa sobre los últimos "
            "~100 días disponibles de un activo (límite del plan gratuito de datos, no "
            "años de historia): mide qué retorno tuvo el precio 5 y 20 días después de "
            "cada vez que el RSI cruzó por debajo de 30 o por encima de 70 en esa ventana, "
            "con tasa de acierto. Úsala cuando el usuario pregunte qué tan confiable es "
            "una señal o pida evidencia en vez de solo el estado actual. Es estadística "
            "descriptiva sobre una muestra reciente y chica, no una garantía ni una "
            "predicción — acláraselo al usuario, y menciona si el sample_size es bajo."
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
    "backtest_rsi_signal": lambda symbol: backtest_rsi_signal(symbol),
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


MAX_HISTORY_MESSAGES = 12

# La instrucción de idioma puesta solo en SYSTEM_PROMPT no basta: el resto
# del prompt (tools, descripciones) está en español y ahoga esa instrucción
# — probado en vivo, el modelo seguía respondiendo en español a preguntas en
# inglés. Por eso se refuerza por turno con detección real de idioma,
# inyectada directamente en el mensaje del usuario (el modelo obedece mucho
# mejor una instrucción en el turno actual que una enterrada en el system
# prompt junto a un montón de texto en el otro idioma).
LANGUAGE_DIRECTIVES = {
    "en": (
        "[Reply entirely in English for this message. Do not use any "
        "Spanish, even though tool names/descriptions are in Spanish.]\n\n"
    ),
    "es": "[Responde enteramente en español para este mensaje.]\n\n",
}


def _reply_language_directive(text: str) -> str:
    try:
        lang = detect(text)
    except LangDetectException:
        lang = "es"
    return LANGUAGE_DIRECTIVES["en" if lang == "en" else "es"]


def ask(question: str, history: list[dict] | None = None, image: dict | None = None) -> dict:
    """Envía una pregunta al agente y devuelve {"text": ..., "news": [...]},
    resolviendo internamente cualquier llamada a tools que Claude decida
    hacer. `news` trae los artículos que el agente haya consultado con
    get_news durante la conversación, para mostrarlos como tarjetas en la UI
    en vez de solo texto plano.

    `history` son los turnos previos (formato [{"role": "user"|"assistant",
    "content": str}, ...], sin las llamadas a tools internas) para que el
    agente pueda resolver preguntas de seguimiento ("¿y el RSI?") con
    contexto real. Se recorta a los últimos MAX_HISTORY_MESSAGES para no
    dejar crecer el costo de tokens sin límite en una conversación larga.

    `image`, si se pasa, es {"media_type": "image/png", "data": <base64>} —
    un screenshot de chart que Claude analiza directamente con su visión
    nativa (no es una tool, es comprensión multimodal del mensaje mismo).
    Solo aplica al turno actual, no se reenvía en `history` en turnos
    futuros para no inflar el costo de tokens de la conversación."""
    past_turns = [
        {"role": turn["role"], "content": turn["content"]}
        for turn in (history or [])[-MAX_HISTORY_MESSAGES:]
    ]

    directive = _reply_language_directive(question)

    if image:
        current_turn_content = [
            {
                "type": "image",
                "source": {"type": "base64", "media_type": image["media_type"], "data": image["data"]},
            },
            {"type": "text", "text": directive + question},
        ]
    else:
        current_turn_content = directive + question

    messages = past_turns + [{"role": "user", "content": current_turn_content}]
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
