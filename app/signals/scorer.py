_WEIGHTS = {
    "rsi": 0.25,
    "macd": 0.20,
    "ma_cross": 0.20,
    "bollinger": 0.15,
    "volume": 0.10,
    "support_resistance": 0.10,
}
_SENTIMENT_WEIGHT = 0.15


def calculate_score(indicators: dict, sentiment_score: float) -> int:
    """
    Compute composite signal score 0-100.
    sentiment_score: float from -1.0 (very negative) to 1.0 (very positive).
    """
    raw = 0.0

    rsi = indicators["rsi"]
    if rsi <= 30:
        rsi_raw = 1.0
    elif rsi >= 70:
        rsi_raw = -1.0
    else:
        rsi_raw = -((rsi - 50) / 20)
    raw += rsi_raw * _WEIGHTS["rsi"]

    macd_map = {"bullish": 1.0, "neutral": 0.0, "bearish": -1.0}
    raw += macd_map[indicators["macd_signal"]] * _WEIGHTS["macd"]

    ma_map = {"golden": 1.0, "none": 0.0, "death": -1.0}
    raw += ma_map[indicators["ma_cross"]] * _WEIGHTS["ma_cross"]

    bb_map = {"lower": 1.0, "mid": 0.0, "upper": -1.0}
    raw += bb_map[indicators["bb_position"]] * _WEIGHTS["bollinger"]

    raw += (0.5 if indicators["volume_surge"] else 0.0) * _WEIGHTS["volume"]

    sr_raw = 0.0
    if indicators["near_support"]:
        sr_raw += 1.0
    if indicators["near_resistance"]:
        sr_raw -= 1.0
    raw += sr_raw * _WEIGHTS["support_resistance"]

    base_score = (raw + 1.0) / 2.0 * 100.0
    sentiment_adj = float(sentiment_score) * _SENTIMENT_WEIGHT * 100.0
    final = base_score + sentiment_adj

    return int(max(0, min(100, round(final))))
