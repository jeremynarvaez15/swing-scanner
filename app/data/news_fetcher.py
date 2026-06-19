import requests
from datetime import datetime, timedelta

_FINANCIAL_SOURCES = (
    "cnbc.com,reuters.com,marketwatch.com,thestreet.com,"
    "seekingalpha.com,benzinga.com,apnews.com"
)


def fetch_news(tickers: list[str], api_key: str) -> dict[str, list[dict]]:
    """
    Fetch recent headlines for each ticker from NewsAPI.
    Batches tickers to stay within free tier (100 calls/day).
    Returns dict: ticker -> list of headline dicts.
    """
    results = {t: [] for t in tickers}
    if not api_key:
        return results

    since = (datetime.utcnow() - timedelta(hours=24)).strftime("%Y-%m-%dT%H:%M:%SZ")

    batch_size = 5
    for i in range(0, len(tickers), batch_size):
        batch = tickers[i:i + batch_size]
        query = " OR ".join(batch)
        params = {
            "q": query,
            "from": since,
            "sortBy": "publishedAt",
            "language": "en",
            "domains": _FINANCIAL_SOURCES,
            "pageSize": 20,
            "apiKey": api_key,
        }
        try:
            resp = requests.get("https://newsapi.org/v2/everything", params=params, timeout=10)
            resp.raise_for_status()
            articles = resp.json().get("articles", [])
            for article in articles:
                title = article.get("title", "")
                for ticker in batch:
                    if ticker.upper() in title.upper():
                        results[ticker].append({
                            "title": title,
                            "source": article.get("source", {}).get("name", ""),
                            "published_at": article.get("publishedAt", ""),
                            "url": article.get("url", ""),
                        })
        except requests.RequestException:
            continue

    return results
