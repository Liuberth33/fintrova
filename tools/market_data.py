import os

import requests
from dotenv import load_dotenv

load_dotenv()

ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")

ALPHA_VANTAGE_URL = "https://www.alphavantage.co/query"
SERPAPI_URL = "https://serpapi.com/search"

# Códigos de cripto reconocidos para distinguir un par "BTC/USD" (cripto) de
# uno "EUR/USD" (forex) o "XAU/USD" (metal) — las tres formas comparten el
# mismo formato "X/Y" pero Alpha Vantage las resuelve con funciones distintas
# para el historial (FX_DAILY vs DIGITAL_CURRENCY_DAILY).
CRYPTO_CODES = {
    "BTC", "ETH", "LTC", "XRP", "DOGE", "ADA", "SOL", "BNB", "DOT",
    "MATIC", "AVAX", "LINK", "UNI", "USDT", "USDC",
}

# Nombres comunes de índices -> el ETF más líquido que los replica. Alpha
# Vantage no ofrece datos de índice crudo (^GSPC, etc.) en su plan gratuito,
# así que se sirven vía el ETF de referencia, igual que haría un bróker retail.
INDEX_ALIASES = {
    "SP500": "SPY", "S&P500": "SPY", "S&P 500": "SPY", "^GSPC": "SPY", "SPX": "SPY",
    "NASDAQ": "QQQ", "NASDAQ100": "QQQ", "NASDAQ 100": "QQQ", "^IXIC": "QQQ", "^NDX": "QQQ",
    "DOW": "DIA", "DOWJONES": "DIA", "DOW JONES": "DIA", "^DJI": "DIA",
    "RUSSELL2000": "IWM", "RUSSELL 2000": "IWM", "^RUT": "IWM",
}

# Nombre común -> (función de materias primas de Alpha Vantage, granularidad
# soportada). WTI/BRENT/NATURAL_GAS sí tienen datos diarios; metales y
# agrícolas de Alpha Vantage solo vienen a granularidad mensual.
COMMODITY_FUNCTIONS = {
    "OIL": ("WTI", "daily"), "WTI": ("WTI", "daily"),
    "CRUDE": ("WTI", "daily"), "CRUDE OIL": ("WTI", "daily"),
    "BRENT": ("BRENT", "daily"), "BRENT OIL": ("BRENT", "daily"),
    "GAS": ("NATURAL_GAS", "daily"), "NATGAS": ("NATURAL_GAS", "daily"),
    "NATURAL GAS": ("NATURAL_GAS", "daily"), "NATURAL_GAS": ("NATURAL_GAS", "daily"),
    "COPPER": ("COPPER", "monthly"),
    "ALUMINUM": ("ALUMINUM", "monthly"), "ALUMINIUM": ("ALUMINUM", "monthly"),
    "WHEAT": ("WHEAT", "monthly"),
    "CORN": ("CORN", "monthly"),
    "COTTON": ("COTTON", "monthly"),
    "SUGAR": ("SUGAR", "monthly"),
    "COFFEE": ("COFFEE", "monthly"),
}

# Algunos ETF/índices no cotizan en NASDAQ, que es el exchange que
# _to_google_finance_query asume por defecto para tickers sin ":".
GOOGLE_FINANCE_EXCHANGE_OVERRIDES = {
    "SPY": "AMEX", "DIA": "AMEX", "IWM": "AMEX",
}


def _normalize(symbol: str) -> str:
    return symbol.strip().upper()


def _resolve_alias(symbol: str) -> str:
    """Traduce nombres comunes de índices a su ETF de referencia, que es el
    símbolo que las APIs de mercado realmente entienden."""
    normalized = _normalize(symbol)
    if normalized in INDEX_ALIASES:
        return INDEX_ALIASES[normalized]
    return symbol


def _is_forex_pair(symbol: str) -> bool:
    return "/" in symbol


def _is_crypto_pair(symbol: str) -> bool:
    if not _is_forex_pair(symbol):
        return False
    from_currency = symbol.upper().split("/")[0]
    return from_currency in CRYPTO_CODES


def _is_commodity(symbol: str) -> bool:
    return _normalize(symbol) in COMMODITY_FUNCTIONS


def _alpha_vantage_get(params: dict) -> dict:
    """Llama a Alpha Vantage y traduce sus respuestas de error (símbolo
    inválido, límite de rate alcanzado) a una excepción con un mensaje claro,
    en vez de dejar que el KeyError críptico de más adelante llegue al agente."""
    response = requests.get(ALPHA_VANTAGE_URL, params=params, timeout=10)
    response.raise_for_status()
    payload = response.json()

    for error_key in ("Error Message", "Note", "Information"):
        if error_key in payload:
            raise RuntimeError(f"Alpha Vantage: {payload[error_key]}")

    return payload


def _get_commodity_series(name: str) -> tuple[str, dict]:
    function, interval = COMMODITY_FUNCTIONS[_normalize(name)]
    payload = _alpha_vantage_get({
        "function": function,
        "interval": interval,
        "apikey": ALPHA_VANTAGE_API_KEY,
    })
    data = payload.get("data")
    if not data:
        raise RuntimeError(f"Alpha Vantage no devolvió datos de materia prima para '{name}'.")
    return payload.get("name", name), data


def get_price(symbol: str) -> dict:
    """Precio actual de un activo: acción, índice (vía su ETF de
    referencia), forex, cripto o materia prima."""
    original = symbol
    resolved = _resolve_alias(symbol)

    if _is_commodity(resolved):
        name, data = _get_commodity_series(resolved)
        latest = data[0]
        return {
            "symbol": name,
            "price": float(latest["value"]),
            "date": latest["date"],
        }

    if _is_forex_pair(resolved):
        from_currency, to_currency = resolved.upper().split("/")
        params = {
            "function": "CURRENCY_EXCHANGE_RATE",
            "from_currency": from_currency,
            "to_currency": to_currency,
            "apikey": ALPHA_VANTAGE_API_KEY,
        }
        rate = _alpha_vantage_get(params)["Realtime Currency Exchange Rate"]

        return {
            "symbol": f"{from_currency}/{to_currency}",
            "price": float(rate["5. Exchange Rate"]),
            "last_refreshed": rate["6. Last Refreshed"],
        }

    params = {
        "function": "GLOBAL_QUOTE",
        "symbol": resolved.upper(),
        "apikey": ALPHA_VANTAGE_API_KEY,
    }
    quote = _alpha_vantage_get(params).get("Global Quote")
    if not quote:
        raise RuntimeError(f"Alpha Vantage no devolvió datos para el símbolo '{original}'. ¿Es un ticker válido?")

    result = {
        "symbol": quote["01. symbol"],
        "price": float(quote["05. price"]),
        "change": float(quote["09. change"]),
        "change_percent": quote["10. change percent"],
        "volume": int(quote["06. volume"]),
        "latest_trading_day": quote["07. latest trading day"],
    }
    if resolved != original:
        result["tracked_via"] = f"{original} se sigue vía el ETF {resolved}"
    return result


def get_history(symbol: str, days: int = 30) -> list[dict]:
    """Historial de precios de los últimos `days` días/períodos. Acepta
    acciones, índices (vía ETF), forex, cripto y materias primas. Para
    materias primas que solo tienen granularidad mensual, `days` se
    interpreta como número de períodos, no de días calendario."""
    original = symbol
    resolved = _resolve_alias(symbol)

    if _is_commodity(resolved):
        _, data = _get_commodity_series(resolved)
        return [
            {"date": point["date"], "close": float(point["value"])}
            for point in data[:days]
        ]

    if _is_crypto_pair(resolved):
        from_currency, to_currency = resolved.upper().split("/")
        params = {
            "function": "DIGITAL_CURRENCY_DAILY",
            "symbol": from_currency,
            "market": to_currency,
            "apikey": ALPHA_VANTAGE_API_KEY,
        }
        series = _alpha_vantage_get(params).get("Time Series (Digital Currency Daily)")
    elif _is_forex_pair(resolved):
        from_currency, to_currency = resolved.upper().split("/")
        params = {
            "function": "FX_DAILY",
            "from_symbol": from_currency,
            "to_symbol": to_currency,
            "outputsize": "compact",
            "apikey": ALPHA_VANTAGE_API_KEY,
        }
        series = _alpha_vantage_get(params).get("Time Series FX (Daily)")
    else:
        params = {
            "function": "TIME_SERIES_DAILY",
            "symbol": resolved.upper(),
            "outputsize": "compact",
            "apikey": ALPHA_VANTAGE_API_KEY,
        }
        series = _alpha_vantage_get(params).get("Time Series (Daily)")

    if not series:
        raise RuntimeError(f"Alpha Vantage no devolvió historial para el símbolo '{original}'. ¿Es un ticker válido?")

    history = [
        {
            "date": date,
            "open": float(values["1. open"]),
            "high": float(values["2. high"]),
            "low": float(values["3. low"]),
            "close": float(values["4. close"]),
        }
        for date, values in series.items()
    ]
    history.sort(key=lambda entry: entry["date"], reverse=True)
    return history[:days]


def _to_google_finance_query(symbol: str) -> str:
    if _is_forex_pair(symbol):
        from_currency, to_currency = symbol.upper().split("/")
        return f"{from_currency}-{to_currency}"
    normalized = _normalize(symbol)
    if normalized in GOOGLE_FINANCE_EXCHANGE_OVERRIDES:
        return f"{normalized}:{GOOGLE_FINANCE_EXCHANGE_OVERRIDES[normalized]}"
    if ":" in symbol:
        return symbol.upper()
    return f"{symbol.upper()}:NASDAQ"


def get_news(symbol: str, limit: int = 5) -> list[dict]:
    """Noticias financieras recientes relacionadas a un activo. Mejor
    cobertura en acciones, índices, forex y cripto; para materias primas
    Google Finance suele tener poco o ningún resultado directo."""
    resolved = _resolve_alias(symbol)
    params = {
        "engine": "google_finance",
        "q": _to_google_finance_query(resolved),
        "api_key": SERPAPI_API_KEY,
    }
    response = requests.get(SERPAPI_URL, params=params, timeout=10)
    response.raise_for_status()
    articles = response.json().get("news_results", [])

    return [
        {
            "title": article.get("snippet"),
            "source": article.get("source"),
            "date": article.get("date"),
            "link": article.get("link"),
        }
        for article in articles[:limit]
    ]
