from app.signals.scorer import calculate_score

def _bullish():
    return {"rsi": 28.0, "macd_signal": "bullish", "ma_cross": "golden",
            "bb_position": "lower", "volume_surge": True, "near_support": True, "near_resistance": False}

def _bearish():
    return {"rsi": 75.0, "macd_signal": "bearish", "ma_cross": "death",
            "bb_position": "upper", "volume_surge": False, "near_support": False, "near_resistance": True}

def _neutral():
    return {"rsi": 50.0, "macd_signal": "neutral", "ma_cross": "none",
            "bb_position": "mid", "volume_surge": False, "near_support": False, "near_resistance": False}

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
