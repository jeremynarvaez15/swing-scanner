import yfinance as yf
import pandas as pd
from datetime import datetime, timezone


def get_stock_details(ticker: str, df: pd.DataFrame) -> dict:
    """
    Fetch enriched details for a single ticker: ATR, 52-week position,
    earnings date, sector, and simple price targets.
    Only called for watchlist stocks to stay within API limits.
    """
    details = {
        "atr": None,
        "week52_pct": None,
        "week52_low": None,
        "week52_high": None,
        "days_to_earnings": None,
        "sector": "N/A",
        "target_up": None,
        "target_down": None,
        "short_pct": None,
        "short_ratio": None,
    }

    try:
        # ATR (14-day Average True Range)
        high = df["High"]
        low = df["Low"]
        close = df["Close"]
        tr = pd.concat([
            high - low,
            (high - close.shift()).abs(),
            (low - close.shift()).abs(),
        ], axis=1).max(axis=1)
        details["atr"] = round(float(tr.rolling(14).mean().iloc[-1]), 2)

        # 52-week position
        year_high = float(high.max())
        year_low = float(low.min())
        current = float(close.iloc[-1])
        rng = year_high - year_low
        details["week52_low"] = round(year_low, 2)
        details["week52_high"] = round(year_high, 2)
        details["week52_pct"] = round((current - year_low) / rng * 100, 1) if rng > 0 else 50.0

        # Price targets: resistance = 52w high, support = 52w low
        # Simple target: nearest 5% move up/down from current
        details["target_up"] = round(year_high, 2)
        details["target_down"] = round(year_low, 2)
    except Exception:
        pass

    try:
        t = yf.Ticker(ticker)
        info = t.info
        details["sector"] = info.get("sector", "N/A")
        try:
            raw_short_pct = info.get("shortPercentOfFloat")
            if isinstance(raw_short_pct, (int, float)):
                details["short_pct"] = round(float(raw_short_pct) * 100, 1)
        except Exception:
            pass
        try:
            raw_short_ratio = info.get("shortRatio")
            if isinstance(raw_short_ratio, (int, float)):
                details["short_ratio"] = round(float(raw_short_ratio), 1)
        except Exception:
            pass

        # Earnings date
        cal = t.calendar
        if cal is not None and not cal.empty:
            earnings_col = [c for c in cal.columns if "Earnings" in str(c)]
            if earnings_col:
                earnings_date = cal[earnings_col[0]].iloc[0]
                if hasattr(earnings_date, "to_pydatetime"):
                    earnings_date = earnings_date.to_pydatetime()
                if earnings_date:
                    now = datetime.now(timezone.utc)
                    if hasattr(earnings_date, "tzinfo") and earnings_date.tzinfo is None:
                        earnings_date = earnings_date.replace(tzinfo=timezone.utc)
                    days = (earnings_date - now).days
                    if 0 <= days <= 60:
                        details["days_to_earnings"] = days
    except Exception:
        pass

    return details


def fetch_price_data(tickers: list[str]) -> tuple[dict[str, pd.DataFrame], pd.DataFrame]:
    """
    Download 1 year of daily OHLCV for all tickers + SPY in one API call.
    Returns (dict keyed by ticker symbol, spy_df).
    SPY is excluded from the result dict but returned separately for RS calculation.
    """
    all_symbols = list(set(tickers) | {"SPY"})
    raw = yf.download(
        tickers=all_symbols,
        period="1y",
        interval="1d",
        group_by="ticker",
        auto_adjust=True,
        threads=True,
        progress=False,
    )

    result = {}
    spy_df = pd.DataFrame()

    if len(all_symbols) == 1:
        # Only happens if tickers=["SPY"]
        df = raw[["Open", "High", "Low", "Close", "Volume"]].copy()
        df.dropna(inplace=True)
        spy_df = df
    else:
        for ticker in all_symbols:
            try:
                df = raw[ticker][["Open", "High", "Low", "Close", "Volume"]].copy()
                df.dropna(inplace=True)
                if len(df) == 0:
                    continue
                if ticker == "SPY":
                    spy_df = df
                else:
                    result[ticker] = df
            except KeyError:
                continue

    return result, spy_df


def get_current_price(ticker: str) -> dict:
    """Get current price, daily change %, and volume for a single ticker."""
    info = yf.Ticker(ticker).fast_info
    price = float(info.last_price)
    prev_close = float(info.previous_close)
    change_pct = ((price - prev_close) / prev_close) * 100 if prev_close else 0.0
    volume = int(info.three_month_average_volume or 0)
    return {
        "price": round(price, 2),
        "change_pct": round(change_pct, 2),
        "volume": volume,
    }
