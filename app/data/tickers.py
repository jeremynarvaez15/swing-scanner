import io
import pandas as pd
import requests
from functools import lru_cache

_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; SwingScanner/1.0)"}


def _read_html_with_headers(url: str) -> list[pd.DataFrame]:
    resp = requests.get(url, headers=_HEADERS, timeout=15)
    resp.raise_for_status()
    return pd.read_html(io.StringIO(resp.text))


@lru_cache(maxsize=1)
def get_sp500_tickers() -> list[str]:
    """Fetch S&P 500 tickers from Wikipedia."""
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    tables = _read_html_with_headers(url)
    df = tables[0]
    tickers = df["Symbol"].str.replace(".", "-", regex=False).tolist()
    return sorted(set(tickers))

@lru_cache(maxsize=1)
def get_nasdaq100_tickers() -> list[str]:
    """Fetch NASDAQ-100 tickers from Wikipedia."""
    url = "https://en.wikipedia.org/wiki/Nasdaq-100"
    tables = _read_html_with_headers(url)
    for table in tables:
        if "Ticker" in table.columns:
            tickers = table["Ticker"].str.replace(".", "-", regex=False).tolist()
            return sorted(set(tickers))
    raise ValueError("Could not find NASDAQ-100 ticker table on Wikipedia")

def get_all_tickers() -> list[str]:
    """Return deduplicated union of S&P 500 and NASDAQ-100."""
    combined = set(get_sp500_tickers()) | set(get_nasdaq100_tickers())
    return sorted(combined)
