import streamlit as st
from datetime import datetime, timezone

from app.data.sp100_tickers import get_sp100_tickers


def _score_badge(score: int) -> str:
    if score >= 9:
        return f"🔴 [{score}]"
    if score >= 7:
        return f"🟠 [{score}]"
    if score >= 5:
        return f"🟡 [{score}]"
    return f"⚪ [{score}]"


def _direction_icon(direction: str) -> str:
    return {"bullish": "🟢", "bearish": "🔴", "neutral": "⚪"}.get(direction, "⚪")


def _time_ago(published_at: str) -> str:
    if not published_at:
        return ""
    try:
        dt = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
        delta = datetime.now(timezone.utc) - dt
        hours = int(delta.total_seconds() // 3600)
        minutes = int((delta.total_seconds() % 3600) // 60)
        if hours >= 1:
            return f"{hours}h ago"
        return f"{minutes}m ago"
    except Exception:
        return ""


def _render_article_card(article: dict):
    score = article.get("impact_score", 5)
    direction = article.get("impact_direction", "neutral")
    ai_tag = article.get("ai_trade_tag", False)
    summary = article.get("summary", "")
    title = article.get("title", "")
    url = article.get("url", "#")
    source = article.get("source", "")
    pub = _time_ago(article.get("published_at", ""))

    badges = f"{_score_badge(score)} {_direction_icon(direction)}"
    if ai_tag:
        badges += " 🤖"

    st.markdown(f"**{badges} {title}**")
    if summary:
        st.caption(summary)
    meta = " · ".join(filter(None, [source, pub]))
    st.markdown(f"[Read Full Article →]({url})  *{meta}*")
    st.divider()


def _render_market_feed(summaries: list[dict]):
    market = [a for a in summaries if a.get("category") == "market"]
    market.sort(key=lambda a: a.get("impact_score", 0), reverse=True)

    st.subheader("🌍 Market Intelligence Feed")
    st.caption("Global business, world events, and market news — ranked by impact")

    if not market:
        st.info("No macro news articles available. Check your NewsAPI key.")
        return

    top20 = market[:20]
    for article in top20:
        _render_article_card(article)

    if len(market) > 20:
        with st.expander(f"Show {len(market) - 20} more articles"):
            for article in market[20:]:
                _render_article_card(article)


def _render_ai_watch(summaries: list[dict]):
    ai_articles = [
        a for a in summaries
        if a.get("ai_trade_tag") or a.get("category") == "ai"
    ]
    seen = set()
    unique = []
    for a in ai_articles:
        if a["url"] not in seen:
            seen.add(a["url"])
            unique.append(a)
    ai_articles = unique
    ai_articles.sort(key=lambda a: a.get("impact_score", 0), reverse=True)

    st.subheader("🤖 AI & NVDA Watch")
    st.caption("Stories impacting the AI trade: NVDA, AMD, AVGO, MSFT, GOOGL, META")

    if not ai_articles:
        st.info("No AI-specific stories in the last hour. Check back soon.")
        return

    bull = sum(1 for a in ai_articles if a.get("impact_direction") == "bullish")
    bear = sum(1 for a in ai_articles if a.get("impact_direction") == "bearish")
    neut = sum(1 for a in ai_articles if a.get("impact_direction") == "neutral")
    st.caption(f"*{bull} bullish · {bear} bearish · {neut} neutral AI stories today*")

    for article in ai_articles:
        _render_article_card(article)


def _render_stock_news(summaries: list[dict]):
    st.subheader("📊 Your Stocks")
    st.caption("News grouped by company — S&P 100 + CIFR")

    company_map: dict[str, list[dict]] = {}
    for a in summaries:
        ticker = a.get("ticker")
        if ticker:
            company_map.setdefault(ticker, []).append(a)

    sp100 = get_sp100_tickers()
    for entry in sp100:
        ticker = entry["ticker"]
        name = entry["name"]
        articles = company_map.get(ticker, [])
        if not articles:
            continue
        articles.sort(key=lambda a: a.get("impact_score", 0), reverse=True)
        label = f"**{ticker}** — {name} ({len(articles)} article{'s' if len(articles) > 1 else ''})"
        with st.expander(label, expanded=(ticker == "CIFR")):
            for article in articles[:3]:
                _render_article_card(article)


def render_news_digest(summaries: list[dict]):
    if not summaries:
        st.warning("No news data available. Make sure NEWS_API_KEY is set in your Streamlit secrets.")
        return

    _render_market_feed(summaries)
    st.divider()
    _render_ai_watch(summaries)
    st.divider()
    _render_stock_news(summaries)
