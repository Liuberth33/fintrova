RSI_OVERSOLD = 30
RSI_OVERBOUGHT = 70


def generate_alert(indicators: dict) -> list[dict]:
    """Evalúa los indicadores (formato devuelto por
    indicators.calculate_indicators) contra reglas técnicas simples y
    devuelve las alertas detectadas. Cada alerta indica un tipo, una
    señal (compra/venta) y un mensaje legible."""
    alerts = []

    rsi = indicators.get("rsi_14")
    if rsi is not None:
        if rsi <= RSI_OVERSOLD:
            alerts.append({
                "type": "rsi_oversold",
                "signal": "compra",
                "message": f"RSI(14) en {rsi} — zona de sobreventa",
            })
        elif rsi >= RSI_OVERBOUGHT:
            alerts.append({
                "type": "rsi_overbought",
                "signal": "venta",
                "message": f"RSI(14) en {rsi} — zona de sobrecompra",
            })

    macd = indicators.get("macd")
    if macd is not None:
        histogram = macd["histogram"]
        if histogram > 0:
            alerts.append({
                "type": "macd_bullish",
                "signal": "compra",
                "message": f"MACD por encima de la señal (histograma {histogram}) — momentum alcista",
            })
        elif histogram < 0:
            alerts.append({
                "type": "macd_bearish",
                "signal": "venta",
                "message": f"MACD por debajo de la señal (histograma {histogram}) — momentum bajista",
            })

    sma_20 = indicators.get("sma_20")
    sma_50 = indicators.get("sma_50")
    if sma_20 is not None and sma_50 is not None:
        if sma_20 > sma_50:
            alerts.append({
                "type": "trend_bullish",
                "signal": "compra",
                "message": f"SMA20 ({sma_20}) por encima de SMA50 ({sma_50}) — tendencia alcista",
            })
        elif sma_20 < sma_50:
            alerts.append({
                "type": "trend_bearish",
                "signal": "venta",
                "message": f"SMA20 ({sma_20}) por debajo de SMA50 ({sma_50}) — tendencia bajista",
            })

    return alerts
