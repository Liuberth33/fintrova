import pandas as pd


def _to_frame(history: list[dict]) -> pd.DataFrame:
    frame = pd.DataFrame(history)
    frame["date"] = pd.to_datetime(frame["date"])
    return frame.sort_values("date")


def _sma(closes: pd.Series, window: int) -> float | None:
    if len(closes) < window:
        return None
    return round(closes.rolling(window).mean().iloc[-1], 4)


def _rsi(closes: pd.Series, period: int = 14) -> float | None:
    if len(closes) < period + 1:
        return None
    delta = closes.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean().iloc[-1]
    avg_loss = loss.rolling(period).mean().iloc[-1]
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return round(100 - (100 / (1 + rs)), 2)


def _macd(closes: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> dict | None:
    if len(closes) < slow + signal:
        return None
    ema_fast = closes.ewm(span=fast, adjust=False).mean()
    ema_slow = closes.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line

    return {
        "macd": round(macd_line.iloc[-1], 4),
        "signal": round(signal_line.iloc[-1], 4),
        "histogram": round(histogram.iloc[-1], 4),
    }


def calculate_indicators(history: list[dict]) -> dict:
    """RSI, MACD y medias móviles sobre un historial de precios (formato
    devuelto por market_data.get_history), ordenado cronológicamente antes
    de calcular. Devuelve None en los indicadores que no tienen suficientes
    datos en `history` para calcularse."""
    frame = _to_frame(history)
    closes = frame["close"]

    return {
        "sma_20": _sma(closes, 20),
        "sma_50": _sma(closes, 50),
        "rsi_14": _rsi(closes, 14),
        "macd": _macd(closes),
    }
