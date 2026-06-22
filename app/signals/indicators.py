import pandas as pd
import numpy as np


def _rsi(close: pd.Series, period: int = 14) -> float:
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    rs = gain / loss.replace(0, np.nan)
    rsi_series = 100 - (100 / (1 + rs))
    return round(float(rsi_series.iloc[-1]), 2)


def _macd_signal(close: pd.Series) -> str:
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    macd_line = ema12 - ema26
    signal_line = macd_line.ewm(span=9, adjust=False).mean()
    prev_diff = macd_line.iloc[-2] - signal_line.iloc[-2]
    curr_diff = macd_line.iloc[-1] - signal_line.iloc[-1]
    if prev_diff < 0 and curr_diff >= 0:
        return "bullish"
    if prev_diff > 0 and curr_diff <= 0:
        return "bearish"
    return "neutral"


def _ma_cross(close: pd.Series) -> tuple[str, float, float]:
    if len(close) < 200:
        return "none", round(float(close.rolling(min(50, len(close))).mean().iloc[-1]), 2), float("nan")
    ma50 = close.rolling(50).mean()
    ma200 = close.rolling(200).mean()
    prev_diff = ma50.iloc[-2] - ma200.iloc[-2]
    curr_diff = ma50.iloc[-1] - ma200.iloc[-1]
    if prev_diff < 0 and curr_diff >= 0:
        cross = "golden"
    elif prev_diff > 0 and curr_diff <= 0:
        cross = "death"
    else:
        cross = "none"
    return cross, round(float(ma50.iloc[-1]), 2), round(float(ma200.iloc[-1]), 2)


def _bollinger_position(close: pd.Series, period: int = 20, std_dev: float = 2.0) -> str:
    rolling_mean = close.rolling(period).mean()
    rolling_std = close.rolling(period).std()
    upper = rolling_mean + std_dev * rolling_std
    lower = rolling_mean - std_dev * rolling_std
    price = close.iloc[-1]
    up = upper.iloc[-1]
    lo = lower.iloc[-1]
    band_range = up - lo
    if band_range == 0:
        return "mid"
    position = (price - lo) / band_range
    if position >= 0.8:
        return "upper"
    if position <= 0.2:
        return "lower"
    return "mid"


def _volume_metrics(volume: pd.Series) -> tuple[bool, float]:
    avg_30 = volume.rolling(30).mean().iloc[-1]
    current = volume.iloc[-1]
    if avg_30 == 0:
        return False, 1.0
    ratio = current / avg_30
    return bool(ratio >= 1.5), round(float(ratio), 2)


def _support_resistance(close: pd.Series, threshold_pct: float = 0.02) -> tuple[bool, bool]:
    year_high = close.max()
    year_low = close.min()
    price = close.iloc[-1]
    near_resistance = abs(price - year_high) / year_high <= threshold_pct
    near_support = abs(price - year_low) / year_low <= threshold_pct
    return bool(near_support), bool(near_resistance)


def calculate_indicators(df: pd.DataFrame) -> dict:
    """Calculate all swing trade indicators from OHLCV DataFrame."""
    close = df["Close"]
    volume = df["Volume"]

    rsi = _rsi(close)
    macd_signal = _macd_signal(close)
    ma_cross, ma_50, ma_200 = _ma_cross(close)
    bb_position = _bollinger_position(close)
    volume_surge, volume_ratio = _volume_metrics(volume)
    near_support, near_resistance = _support_resistance(close)
    ma_20 = round(float(close.rolling(20).mean().iloc[-1]), 2) if len(close) >= 20 else round(float(close.mean()), 2)

    return {
        "rsi": rsi,
        "macd_signal": macd_signal,
        "ma_cross": ma_cross,
        "ma_20": ma_20,
        "ma_50": ma_50,
        "ma_200": ma_200,
        "bb_position": bb_position,
        "volume_surge": volume_surge,
        "volume_ratio": volume_ratio,
        "near_support": near_support,
        "near_resistance": near_resistance,
    }
