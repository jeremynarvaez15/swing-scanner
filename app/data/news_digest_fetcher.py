import feedparser
from datetime import datetime, timezone, timedelta

_FEEDS = [
    # Finance & Markets
    {"url": "https://www.cnbc.com/id/100003114/device/rss/rss.html", "source": "CNBC"},
    {"url": "https://www.cnbc.com/id/20910258/device/rss/rss.html", "source": "CNBC Markets"},
    {"url": "https://feeds.content.dowjones.io/public/rss/mw_realtimeheadlines", "source": "MarketWatch"},
    {"url": "https://finance.yahoo.com/rss/topstories", "source": "Yahoo Finance"},
    {"url": "https://feeds.reuters.com/reuters/businessNews", "source": "Reuters"},
    {"url": "https://markets.businessinsider.com/rss/news", "source": "Business Insider"},
    {"url": "https://feeds.bbci.co.uk/news/world/rss.xml", "source": "BBC News"},
    {"url": "https://apnews.com/apf-business", "source": "AP News"},
    # AI & Tech
    {"url": "https://techcrunch.com/category/artificial-intelligence/feed/", "source": "TechCrunch AI"},
    {"url": "https://www.technologyreview.com/feed/", "source": "MIT Technology Review"},
    {"url": "https://venturebeat.com/category/ai/feed/", "source": "VentureBeat AI"},
    {"url": "https://www.theverge.com/rss/index.xml", "source": "The Verge"},
]

_AI_KEYWORDS = {
    "artificial intelligence", "ai ", " ai", "nvidia", "semiconductor", "gpu",
    "blackwell", "data center", "amd chip", "broadcom", "avgo", "microsoft ai",
    "google ai", "meta ai", "openai", "chatgpt", "machine learning", "deep learning",
    "large language model", "llm", "generative ai", "chip", "techcrunch ai",
    "venturebeat", "mit technology", "neural network",
}

_MARKET_KEYWORDS = {
    "federal reserve", "fed ", "interest rate", "inflation", "recession", "gdp",
    "tariff", "china economy", "oil price", "geopolit", "earnings", "s&p",
    "stock market", "treasury", "jobs report", "dow jones", "nasdaq", "wall street",
    "economy", "economic", "market", "trade", "bond", "yield", "debt",
}

_AI_TECH_SOURCES = {"TechCrunch AI", "VentureBeat AI", "MIT Technology Review"}


def _parse_date(entry) -> str:
    for attr in ("published_parsed", "updated_parsed"):
        t = getattr(entry, attr, None)
        if t:
            try:
                dt = datetime(*t[:6], tzinfo=timezone.utc)
                return dt.isoformat()
            except Exception:
                pass
    return datetime.now(timezone.utc).isoformat()


def _is_recent(entry, hours: int = 48) -> bool:
    for attr in ("published_parsed", "updated_parsed"):
        t = getattr(entry, attr, None)
        if t:
            try:
                dt = datetime(*t[:6], tzinfo=timezone.utc)
                return datetime.now(timezone.utc) - dt < timedelta(hours=hours)
            except Exception:
                pass
    return True


def _categorize(title: str, description: str, source: str) -> str:
    text = (title + " " + description + " " + source).lower()
    if source in _AI_TECH_SOURCES:
        return "ai"
    for kw in _AI_KEYWORDS:
        if kw in text:
            return "ai"
    return "market"


def _fetch_feed(feed_cfg: dict) -> list[dict]:
    try:
        parsed = feedparser.parse(feed_cfg["url"])
        articles = []
        for entry in parsed.entries:
            if not _is_recent(entry):
                continue
            title = getattr(entry, "title", "") or ""
            description = getattr(entry, "summary", "") or getattr(entry, "description", "") or ""
            url = getattr(entry, "link", "") or ""
            if not title or not url:
                continue
            source = feed_cfg["source"]
            articles.append({
                "title": title,
                "description": description[:500],
                "url": url,
                "source": source,
                "published_at": _parse_date(entry),
                "category": _categorize(title, description, source),
                "ticker": None,
            })
        return articles
    except Exception:
        return []


def fetch_market_news() -> list[dict]:
    articles = []
    for feed in _FEEDS:
        articles.extend(_fetch_feed(feed))
    seen = set()
    unique = []
    for a in articles:
        if a["title"] not in seen:
            seen.add(a["title"])
            unique.append(a)
    return unique


def fetch_ai_news() -> list[dict]:
    return [a for a in fetch_market_news() if a["category"] == "ai"]


_AMBIGUOUS_TICKERS = {
    "T", "F", "C", "V", "D", "L", "A", "K", "O", "R", "M", "PM",
    "ALL", "DD", "DIS", "MA", "SO", "LOW", "BK",
}

_AMBIGUOUS_NAMES = {
    "dow", "general", "united", "american", "national", "digital",
    "global", "international", "first", "allied",
}


def _name_matches(name: str, text: str) -> bool:
    """True only if the full company name appears as a meaningful phrase."""
    name_lower = name.lower().strip()
    words = name_lower.split()
    # Skip very short or ambiguous names
    if len(words) == 1 and (len(name_lower) <= 4 or name_lower in _AMBIGUOUS_NAMES):
        return False
    return name_lower in text


def _ticker_matches(ticker: str, text: str) -> bool:
    """True only if ticker appears as a standalone word (not embedded in another word)."""
    import re
    if ticker in _AMBIGUOUS_TICKERS or len(ticker) <= 1:
        return False
    # Must be surrounded by non-alphanumeric characters or start/end of string
    pattern = r'(?<![a-z0-9])' + re.escape(ticker.lower()) + r'(?![a-z0-9])'
    return bool(re.search(pattern, text))


def fetch_company_news(tickers: list[dict]) -> dict[str, list[dict]]:
    all_articles = fetch_market_news()
    result: dict[str, list[dict]] = {}
    for entry in tickers:
        ticker = entry["ticker"]
        name = entry["name"]
        matches = []
        for a in all_articles:
            text = (a["title"] + " " + a["description"]).lower()
            if _name_matches(name, text) or _ticker_matches(ticker, text):
                matches.append({**a, "ticker": ticker, "category": "company"})
        if matches:
            result[ticker] = matches
    return result
