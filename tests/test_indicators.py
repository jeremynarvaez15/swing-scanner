import pandas as pd
import numpy as np
from app.signals.indicators import calculate_indicators

def _make_df(n=250):
    np.random.seed(42)
    close = 100 + np.cumsum(np.random.randn(n) * 0.5)
    df = pd.DataFrame({
        "Open": close * 0.999,
        "High": close * 1.005,
        "Low": close * 0.995,
        "Close": close,
        "Volume": np.random.randint(1_000_000, 10_000_000, n),
    })
    return df

def test_calculate_indicators_returns_all_keys():
    result = calculate_indicators(_make_df())
    for key in ["rsi", "macd_signal", "ma_cross", "ma_50", "ma_200",
                "bb_position", "volume_surge", "volume_ratio", "near_support", "near_resistance"]:
        assert key in result

def test_rsi_in_range():
    assert 0 <= calculate_indicators(_make_df())["rsi"] <= 100

def test_macd_signal_valid_value():
    assert calculate_indicators(_make_df())["macd_signal"] in ("bullish", "bearish", "neutral")

def test_ma_cross_valid_value():
    assert calculate_indicators(_make_df())["ma_cross"] in ("golden", "death", "none")

def test_bb_position_valid_value():
    assert calculate_indicators(_make_df())["bb_position"] in ("upper", "mid", "lower")

def test_volume_surge_is_bool():
    assert isinstance(calculate_indicators(_make_df())["volume_surge"], bool)
