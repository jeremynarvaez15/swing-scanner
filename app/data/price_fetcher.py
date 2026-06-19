import yfinance as yf
import pandas as pd


def fetch_price_data(tickers: list[str]) -> dict[str, pd.DataFrame]:
    """
    Download 1 year of daily OHLCV for all tickers in one API call.
    Returns dict keyed by ticker symbol.
    """
    raw = yf.download(
        tickers=tickers,
        period="1y",
        interval="1d",
        group_by="ticker",
        auto_adjust=True,
        threads=True,
        progress=False,
    )

    result = {}
    if len(tickers) == 1:
        ticker = tickers[0]
        df = raw[["Open", "High", "Low", "Close", "Volume"]].copy()
        df.dropna(inplace=True)
        result[ticker] = df
    else:
        for ticker in tickers:
            try:
                df = raw[ticker][["Open", "High", "Low", "Close", "Volume"]].copy()
                df.dropna(inplace=True)
                if len(df) > 0:
                    result[ticker] = df
            except KeyError:
                continue

    return result


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
