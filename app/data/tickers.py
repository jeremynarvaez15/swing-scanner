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

_NASDAQ100_FALLBACK = [
    "AAPL","ABNB","ADBE","ADI","ADP","ADSK","AEP","AMAT","AMD","AMGN",
    "AMZN","ANSS","ARM","ASML","AVGO","AZN","BIIB","BKNG","BKR","CCEP",
    "CDNS","CDW","CEG","CMCSA","COST","CPRT","CRWD","CSCO","CSGP","CSX",
    "CTAS","CTSH","DASH","DDOG","DLTR","DXCM","EA","EXC","FANG","FAST",
    "FTNT","GEHC","GFS","GILD","GOOG","GOOGL","HON","IDXX","ILMN","INTC",
    "INTU","ISRG","KDP","KHC","KLAC","LIN","LRCX","LULU","MAR","MCHP",
    "MDB","MDLZ","MELI","META","MNST","MRNA","MRVL","MSFT","MU","NFLX",
    "NVDA","NXP","ODFL","ON","ORLY","PANW","PAYX","PCAR","PDD","PEP",
    "PYPL","QCOM","REGN","ROP","ROST","SBUX","SIRI","SMCI","SNPS","SRPT",
    "TEAM","TMUS","TSLA","TTD","TTWO","TXN","VRSK","VRTX","WBD","WDC","XEL","ZS",
]

@lru_cache(maxsize=1)
def get_nasdaq100_tickers() -> list[str]:
    """Fetch NASDAQ-100 tickers from Wikipedia, fall back to hardcoded list."""
    try:
        url = "https://en.wikipedia.org/wiki/Nasdaq-100"
        tables = _read_html_with_headers(url)
        for table in tables:
            for col in ("Ticker", "Symbol", "Ticker symbol", "Stock Symbol"):
                if col in table.columns:
                    tickers = table[col].dropna().str.replace(".", "-", regex=False).tolist()
                    if len(tickers) >= 90:
                        return sorted(set(tickers))
    except Exception:
        pass
    return sorted(set(_NASDAQ100_FALLBACK))

def get_all_tickers() -> list[str]:
    """Return deduplicated union of S&P 500 and NASDAQ-100."""
    combined = set(get_sp500_tickers()) | set(get_nasdaq100_tickers())
    return sorted(combined)
