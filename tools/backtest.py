import db
from tools.indicators import rsi_series
from tools.market_data import get_history

FORWARD_WINDOWS = (5, 20)  # días hábiles después de cada señal


def _forward_return(closes, index: int, days: int) -> float | None:
    target = index + days
    if target >= len(closes):
        return None
    entry, exit_ = closes[index], closes[target]
    return round((exit_ - entry) / entry * 100, 2)


def _find_signal_crossings(frame, threshold: float, direction: str) -> list[int]:
    """Índices donde el RSI cruza hacia sobreventa (direction='below', RSI
    pasa de >threshold a <=threshold) o sobrecompra (direction='above').
    Solo cuenta el primer día de cada cruce, no cada día que se mantiene
    en esa zona, para no inflar el conteo con una sola señal prolongada."""
    rsi = frame["rsi"]
    crossings = []
    for i in range(1, len(rsi)):
        if direction == "below" and rsi.iloc[i - 1] > threshold >= rsi.iloc[i]:
            crossings.append(i)
        elif direction == "above" and rsi.iloc[i - 1] < threshold <= rsi.iloc[i]:
            crossings.append(i)
    return crossings


def _summarize(frame, indices: list[int]) -> dict:
    closes = frame["close"].tolist()
    summary = {"occurrences": len(indices)}
    for window in FORWARD_WINDOWS:
        returns = [r for i in indices if (r := _forward_return(closes, i, window)) is not None]
        summary[f"avg_return_{window}d_pct"] = round(sum(returns) / len(returns), 2) if returns else None
        summary[f"win_rate_{window}d_pct"] = (
            round(sum(1 for r in returns if r > 0) / len(returns) * 100, 1) if returns else None
        )
        summary[f"sample_size_{window}d"] = len(returns)
    return summary


def backtest_rsi_signal(symbol: str) -> dict:
    """Backtest de las señales de RSI(14) sobrecompra/sobreventa sobre los
    últimos ~100 días disponibles del activo (el máximo del plan gratuito
    de Alpha Vantage — el historial completo de años es una feature premium
    que no tenemos): cada vez que el RSI cruzó por debajo de 30 (sobreventa,
    hipótesis de compra) o por encima de 70 (sobrecompra, hipótesis de
    venta) en esa ventana, mide el retorno del precio 5 y 20 días hábiles
    después. Es una muestra chica, no 20 años de historia — trátalo como
    una señal orientativa reciente, no como estadística robusta, y acláraselo
    al usuario si la muestra (sample_size) es baja.

    Cachea el resultado 24h (los datos diarios no cambian tanto como para
    justificar recalcular en cada pregunta del mismo día)."""
    cache_key = f"rsi_backtest:{symbol.upper()}"
    cached = db.get_cached_backtest(cache_key)
    if cached is not None:
        return cached

    history = get_history(symbol, days=100)
    if len(history) < 60:
        raise RuntimeError(
            f"No hay suficiente historial de '{symbol}' para un backtest confiable "
            f"(solo {len(history)} puntos disponibles, se necesitan al menos 60)."
        )

    frame = rsi_series(history, period=14)
    oversold_idx = _find_signal_crossings(frame, threshold=30, direction="below")
    overbought_idx = _find_signal_crossings(frame, threshold=70, direction="above")

    result = {
        "symbol": symbol,
        "data_points_analyzed": len(frame),
        "date_range": {"from": frame["date"].iloc[0].strftime("%Y-%m-%d"), "to": frame["date"].iloc[-1].strftime("%Y-%m-%d")},
        "rsi_oversold_below_30": _summarize(frame, oversold_idx),
        "rsi_overbought_above_70": _summarize(frame, overbought_idx),
    }

    db.save_backtest_cache(cache_key, result)
    return result
