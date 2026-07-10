_WEIGHTS = {
    "bb_squeeze": 0.20,
    "obv_trend": 0.18,
    "rs_vs_spy": 0.17,
    "consolidation": 0.10,
    "volume": 0.10,
    "rsi": 0.10,
    "macd": 0.08,
    "support_resistance": 0.07,
}
_SENTIMENT_BONUS_MAX = 10.0


def calculate_score(indicators: dict, sentiment_score: float) -> int:
    """
    Compute composite setup score 0-100. Leading indicators weighted first.
    sentiment_score: float from -1.0 (very negative) to 1.0 (very positive).
    """
    raw = 0.0

    # BB Squeeze (leading): squeeze + intensity boost
    if indicators.get("bb_squeeze"):
        intensity = indicators.get("squeeze_intensity", 50)
        squeeze_raw = 0.5 + (intensity / 200.0)  # 0.5 to 1.0
    else:
        squeeze_raw = 0.0
    raw += squeeze_raw * _WEIGHTS["bb_squeeze"]

    # OBV Trend (leading)
    obv_map = {"accumulating": 1.0, "neutral": 0.0, "distributing": -1.0}
    raw += obv_map.get(indicators.get("obv_trend", "neutral"), 0.0) * _WEIGHTS["obv_trend"]

    # Relative Strength vs SPY (leading): clamp to -15/+15 range
    rs = float(indicators.get("rs_vs_spy", 0.0))
    rs_raw = max(-1.0, min(1.0, rs / 15.0))
    raw += rs_raw * _WEIGHTS["rs_vs_spy"]

    # Consolidation (leading)
    consol_map = {"tight": 1.0, "normal": 0.0, "wide": -0.5}
    raw += consol_map.get(indicators.get("consolidation", "normal"), 0.0) * _WEIGHTS["consolidation"]

    # Volume surge (leading)
    raw += (0.5 if indicators.get("volume_surge") else 0.0) * _WEIGHTS["volume"]

    # RSI (mixed)
    rsi = indicators.get("rsi", 50)
    if rsi <= 30:
        rsi_raw = 1.0
    elif rsi >= 70:
        rsi_raw = -1.0
    else:
        rsi_raw = -((rsi - 50) / 20)
    raw += rsi_raw * _WEIGHTS["rsi"]

    # MACD (lagging, reduced)
    macd_map = {"bullish": 1.0, "neutral": 0.0, "bearish": -1.0}
    raw += macd_map.get(indicators.get("macd_signal", "neutral"), 0.0) * _WEIGHTS["macd"]

    # Support/Resistance (leading)
    sr_raw = 0.0
    if indicators.get("near_support"):
        sr_raw += 1.0
    if indicators.get("near_resistance"):
        sr_raw -= 1.0
    raw += sr_raw * _WEIGHTS["support_resistance"]

    # Normalize raw (-1 to 1) → base score (0 to 100)
    # raw theoretical range: sum of all weights = 1.0, so raw in [-1, 1]
    base_score = (raw + 1.0) / 2.0 * 100.0

    # Sentiment bonus: up to +/- 10 points
    sentiment_adj = float(sentiment_score) * _SENTIMENT_BONUS_MAX
    final = base_score + sentiment_adj

    return int(max(0, min(100, round(final))))
