import requests


def fetch_stocktwits_trending() -> list[dict]:
    """
    Fetch trending stocks from StockTwits public API.
    Returns list of dicts with ticker, sentiment, watchers, message_count.
    No API key required.
    """
    try:
        url = "https://api.stocktwits.com/api/2/trending/symbols.json"
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers, timeout=8)
        resp.raise_for_status()
        data = resp.json()
        symbols = data.get("symbols", [])

        results = []
        for s in symbols[:15]:
            ticker = s.get("symbol", "")
            name = s.get("title", ticker)
            watchers = s.get("watchlist_count", 0)

            # Fetch sentiment for this ticker
            sentiment, bullish_pct = _get_ticker_sentiment(ticker)

            results.append({
                "ticker": ticker,
                "name": name,
                "watchers": watchers,
                "sentiment": sentiment,
                "bullish_pct": bullish_pct,
            })

        return results
    except Exception:
        return []


def _get_ticker_sentiment(ticker: str) -> tuple[str, int]:
    """Fetch bullish/bearish sentiment ratio for a ticker from StockTwits."""
    try:
        url = f"https://api.stocktwits.com/api/2/streams/symbol/{ticker}.json"
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers, timeout=6)
        resp.raise_for_status()
        data = resp.json()

        messages = data.get("messages", [])
        bullish = sum(1 for m in messages if m.get("entities", {}).get("sentiment", {}) and
                      m["entities"]["sentiment"].get("basic") == "Bullish")
        bearish = sum(1 for m in messages if m.get("entities", {}).get("sentiment", {}) and
                      m["entities"]["sentiment"].get("basic") == "Bearish")
        total = bullish + bearish

        if total == 0:
            return "neutral", 50

        bullish_pct = int(bullish / total * 100)
        if bullish_pct >= 60:
            return "positive", bullish_pct
        if bullish_pct <= 40:
            return "negative", bullish_pct
        return "neutral", bullish_pct
    except Exception:
        return "neutral", 50
