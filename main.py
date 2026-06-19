import streamlit as st
import time
from datetime import datetime
import pytz

from app.config import load_config, get_twilio_cfg
from app.data.tickers import get_all_tickers
from app.data.price_fetcher import fetch_price_data, get_current_price
from app.data.news_fetcher import fetch_news
from app.data.reddit_fetcher import fetch_reddit_mentions
from app.data.fear_greed import fetch_fear_greed
from app.signals.indicators import calculate_indicators
from app.signals.sentiment import score_sentiment
from app.signals.scorer import calculate_score
from app.alerts.alert_engine import check_and_alert
from app.ui.watchlist import render_watchlist
from app.ui.scanner import render_scanner
from app.ui.sidebar import render_sidebar
from app.ui.settings import render_settings

st.set_page_config(
    page_title="Swing Trade Scanner",
    page_icon="📈",
    layout="wide",
)

_REFRESH_INTERVAL = 15 * 60


def _is_market_open() -> bool:
    et = pytz.timezone("America/New_York")
    now = datetime.now(et)
    if now.weekday() >= 5:
        return False
    market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
    market_close = now.replace(hour=16, minute=0, second=0, microsecond=0)
    return market_open <= now <= market_close


@st.cache_data(ttl=_REFRESH_INTERVAL)
def load_all_data(watchlist: tuple, _cache_buster: int):
    all_tickers = get_all_tickers()
    price_data = fetch_price_data(list(all_tickers))

    news_api_key = st.secrets.get("NEWS_API_KEY", "")
    news_data = fetch_news(list(watchlist), news_api_key) if news_api_key else {}

    reddit_data = {}
    try:
        reddit_data = fetch_reddit_mentions(
            list(watchlist),
            client_id=st.secrets.get("REDDIT_CLIENT_ID", ""),
            client_secret=st.secrets.get("REDDIT_CLIENT_SECRET", ""),
            user_agent=st.secrets.get("REDDIT_USER_AGENT", "SwingScanner/1.0"),
        )
    except Exception:
        pass

    fear_greed = fetch_fear_greed()
    return price_data, news_data, reddit_data, fear_greed


def _build_stock_record(ticker: str, price_data: dict, news_data: dict) -> dict | None:
    df = price_data.get(ticker)
    if df is None or len(df) < 30:
        return None
    try:
        indicators = calculate_indicators(df)
        headlines = news_data.get(ticker, [])
        sentiment = score_sentiment(headlines)
        score = calculate_score(indicators, sentiment["sentiment_score"])
        price_info = get_current_price(ticker)
        return {
            "ticker": ticker,
            "price": price_info["price"],
            "change_pct": price_info["change_pct"],
            "volume": price_info["volume"],
            "score": score,
            "indicators": indicators,
            "sentiment": sentiment,
            "history_df": df,
            **indicators,
            "sentiment_score": sentiment["sentiment_score"],
            "sentiment_label": sentiment["sentiment_label"],
            "news_surge": sentiment["surge"],
            "sector": "N/A",
            "company": ticker,
        }
    except Exception:
        return None


def main():
    st.title("📈 Swing Trade Scanner")
    render_settings()

    if _is_market_open():
        st.success("🟢 Market Open — data refreshes every 15 minutes")
    else:
        st.warning("🔴 Market Closed — showing last session data")

    config = load_config()
    cache_buster = int(time.time() // _REFRESH_INTERVAL)
    watchlist_tuple = tuple(config["watchlist"])

    with st.spinner("Loading market data (this may take 30-60 seconds on first load)..."):
        price_data, news_data, reddit_data, fear_greed = load_all_data(watchlist_tuple, cache_buster)

    render_sidebar(fear_greed, reddit_data)

    watchlist_stocks = []
    for ticker in config["watchlist"]:
        record = _build_stock_record(ticker, price_data, news_data)
        if record:
            watchlist_stocks.append(record)

    render_watchlist(watchlist_stocks)
    st.divider()

    scan_results = []
    all_tickers = list(price_data.keys())
    progress = st.progress(0, text="Building signal scores...")
    for i, ticker in enumerate(all_tickers):
        record = _build_stock_record(ticker, price_data, news_data)
        if record:
            scan_results.append(record)
        if (i + 1) % 10 == 0:
            progress.progress((i + 1) / len(all_tickers))
    progress.empty()

    render_scanner(scan_results)

    if "cooldowns" not in st.session_state:
        st.session_state["cooldowns"] = {}

    twilio_cfg = get_twilio_cfg()
    thresholds = {
        "buy": config["buy_threshold"],
        "sell": config["sell_threshold"],
        "cooldown_hours": config["cooldown_hours"],
    }
    alert_tickers = set(config["watchlist"]) if config["watchlist_only_alerts"] else set(all_tickers)
    if twilio_cfg.get("to_number"):
        for record in scan_results:
            if record["ticker"] in alert_tickers:
                check_and_alert(
                    ticker=record["ticker"],
                    score=record["score"],
                    price=record["price"],
                    indicators=record["indicators"],
                    sentiment=record["sentiment"],
                    thresholds=thresholds,
                    cooldowns=st.session_state["cooldowns"],
                    twilio_cfg=twilio_cfg,
                )


if __name__ == "__main__":
    main()
