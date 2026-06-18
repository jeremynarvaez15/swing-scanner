import pandas as pd
import requests
from functools import lru_cache

@lru_cache(maxsize=1)
def get_sp500_tickers() -> list[str]:
    """Fetch S&P 500 tickers from Wikipedia."""
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    tables = pd.read_html(url)
    df = tables[0]
    tickers = df["Symbol"].str.replace(".", "-", regex=False).tolist()
    return sorted(set(tickers))

@lru_cache(maxsize=1)
def get_nasdaq100_tickers() -> list[str]:
    """Fetch NASDAQ-100 tickers from Wikipedia."""
    url = "https://en.wikipedia.org/wiki/Nasdaq-100"
    tables = pd.read_html(url)
    # Find the table with a 'Ticker' column
    for table in tables:
        if "Ticker" in table.columns:
            tickers = table["Ticker"].str.replace(".", "-", regex=False).tolist()
            return sorted(set(tickers))
    raise ValueError("Could not find NASDAQ-100 ticker table on Wikipedia")

def get_all_tickers() -> list[str]:
    """Return deduplicated union of S&P 500 and NASDAQ-100."""
    combined = set(get_sp500_tickers()) | set(get_nasdaq100_tickers())
    return sorted(combined)
