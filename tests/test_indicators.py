import pandas as pd
import numpy as np
from app.signals.indicators import calculate_indicators, _bb_squeeze, _obv_trend, _consolidation

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
                "bb_position", "volume_surge", "volume_ratio", "near_support", "near_resistance",
                "bb_squeeze", "squeeze_intensity", "obv_trend", "rs_vs_spy", "consolidation", "ma_20"]:
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

def test_bb_squeeze_is_bool():
    result = calculate_indicators(_make_df())
    assert isinstance(result["bb_squeeze"], bool)

def test_squeeze_intensity_in_range():
    result = calculate_indicators(_make_df())
    assert 0 <= result["squeeze_intensity"] <= 100
    assert isinstance(result["squeeze_intensity"], int)

def test_obv_trend_valid_value():
    result = calculate_indicators(_make_df())
    assert result["obv_trend"] in ("accumulating", "distributing", "neutral")

def test_rs_vs_spy_is_float():
    result = calculate_indicators(_make_df())
    assert isinstance(result["rs_vs_spy"], float)

def test_consolidation_valid_value():
    result = calculate_indicators(_make_df())
    assert result["consolidation"] in ("tight", "normal", "wide")

def test_rs_vs_spy_with_spy_df():
    df = _make_df()
    spy_df = _make_df(250)
    result = calculate_indicators(df, spy_df)
    # With SPY data provided, should calculate relative strength
    assert isinstance(result["rs_vs_spy"], float)

def test_rs_vs_spy_without_spy_df():
    df = _make_df()
    result = calculate_indicators(df)
    # Without SPY data, should default to 0.0
    assert result["rs_vs_spy"] == 0.0

def test_bb_squeeze_short_data():
    close = pd.Series([100.0] * 15)
    squeeze, intensity = _bb_squeeze(close)
    assert squeeze is False
    assert intensity == 0

def test_obv_trend_short_data():
    close = pd.Series([100.0, 101.0, 102.0])
    volume = pd.Series([1000, 1000, 1000])
    assert _obv_trend(close, volume) == "neutral"

def test_consolidation_short_data():
    close = pd.Series([100.0] * 30)
    high = pd.Series([101.0] * 30)
    low = pd.Series([99.0] * 30)
    assert _consolidation(high, low, close) == "normal"
