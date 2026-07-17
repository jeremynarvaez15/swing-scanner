import requests
from datetime import datetime, timedelta

_BASE = "https://newsapi.org/v2/everything"

_MACRO_TERMS = [
    "Federal Reserve", "interest rates", "inflation", "recession",
    "GDP", "tariffs", "China economy", "oil prices", "geopolitical",
    "earnings season", "S&P 500", "stock market", "Treasury", "jobs report",
]

_AI_TERMS = [
    "artificial intelligence", "NVIDIA", "semiconductors", "Blackwell",
    "data center", "AI chips", "Broadcom", "AVGO", "AMD chips",
    "Microsoft AI", "Google AI", "Meta AI", "AI spending", "GPU",
]


def _query(api_key: str, q: str, page_size: int = 20) -> list[dict]:
    from_date = (datetime.utcnow() - timedelta(hours=24)).strftime("%Y-%m-%dT%H:%M:%SZ")
    try:
        resp = requests.get(
            _BASE,
            params={
                "q": q,
                "apiKey": api_key,
                "language": "en",
                "sortBy": "publishedAt",
                "pageSize": page_size,
                "from": from_date,
            },
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json().get("articles", [])
    except Exception:
        return []


def _article(raw: dict, category: str, ticker: str | None = None) -> dict:
    return {
        "title": raw.get("title") or "",
        "description": raw.get("description") or raw.get("content") or "",
        "url": raw.get("url") or "",
        "source": (raw.get("source") or {}).get("name") or "Unknown",
        "published_at": raw.get("publishedAt") or "",
        "category": category,
        "ticker": ticker,
    }


def fetch_market_news(api_key: str) -> list[dict]:
    q = " OR ".join(f'"{t}"' for t in _MACRO_TERMS[:8])
    return [_article(r, "market") for r in _query(api_key, q, page_size=20)]


def fetch_ai_news(api_key: str) -> list[dict]:
    q = " OR ".join(f'"{t}"' for t in _AI_TERMS[:8])
    return [_article(r, "ai") for r in _query(api_key, q, page_size=20)]


def fetch_company_news(api_key: str, tickers: list[dict]) -> dict[str, list[dict]]:
    result: dict[str, list[dict]] = {}
    for entry in tickers:
        ticker = entry["ticker"]
        name = entry["name"]
        if ticker == "CIFR":
            q = '"Cipher Digital" OR "CIFR"'
        else:
            q = f'"{name}" OR "{ticker}"'
        articles = _query(api_key, q, page_size=5)
        if articles:
            result[ticker] = [_article(r, "company", ticker) for r in articles]
    return result
