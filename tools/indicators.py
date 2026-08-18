import pandas as pd


def _to_frame(history: list[dict]) -> pd.DataFrame:
    frame = pd.DataFrame(history)
    frame["date"] = pd.to_datetime(frame["date"])
    return frame.sort_values("date")


def _sma(closes: pd.Series, window: int) -> float | None:
    if len(closes) < window:
        return None
    return round(closes.rolling(window).mean().iloc[-1], 4)


def _rsi_series(closes: pd.Series, period: int = 14) -> pd.Series:
    delta = closes.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss.replace(0, float("nan"))
    rsi = 100 - (100 / (1 + rs))
    return rsi.where(avg_loss != 0, 100.0)


def _rsi(closes: pd.Series, period: int = 14) -> float | None:
    if len(closes) < period + 1:
        return None
    value = _rsi_series(closes, period).iloc[-1]
    return round(value, 2) if pd.notna(value) else None


def rsi_series(history: list[dict], period: int = 14) -> pd.DataFrame:
    """Serie completa de RSI a lo largo de todo el historial (no solo el
    último valor), indexada por fecha — pensada para backtesting, donde hay
    que ubicar cada cruce histórico hacia sobrecompra/sobreventa, no solo el
    estado actual."""
    frame = _to_frame(history)
    frame["rsi"] = _rsi_series(frame["close"], period)
    return frame[["date", "close", "rsi"]].dropna(subset=["rsi"]).reset_index(drop=True)


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
