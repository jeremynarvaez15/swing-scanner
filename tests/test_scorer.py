from app.signals.scorer import calculate_score

def _bullish():
    return {"rsi": 28.0, "macd_signal": "bullish", "volume_surge": True,
            "near_support": True, "near_resistance": False, "bb_squeeze": True,
            "squeeze_intensity": 80, "obv_trend": "accumulating", "rs_vs_spy": 10.0,
            "consolidation": "tight"}

def _bearish():
    return {"rsi": 75.0, "macd_signal": "bearish", "volume_surge": False,
            "near_support": False, "near_resistance": True, "bb_squeeze": False,
            "squeeze_intensity": 20, "obv_trend": "distributing", "rs_vs_spy": -12.0,
            "consolidation": "wide"}

def _neutral():
    return {"rsi": 50.0, "macd_signal": "neutral", "volume_surge": False,
            "near_support": False, "near_resistance": False, "bb_squeeze": False,
            "squeeze_intensity": 50, "obv_trend": "neutral", "rs_vs_spy": 0.0,
            "consolidation": "normal"}

def test_score_is_integer_in_range():
    score = calculate_score(_neutral(), 0.0)
    assert isinstance(score, int)
    assert 0 <= score <= 100

def test_bullish_produces_high_score():
    assert calculate_score(_bullish(), 0.8) >= 70

def test_bearish_produces_low_score():
    assert calculate_score(_bearish(), -0.8) <= 30

def test_neutral_produces_mid_score():
    score = calculate_score(_neutral(), 0.0)
    assert 30 <= score <= 70
