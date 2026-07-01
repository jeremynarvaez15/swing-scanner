import streamlit as st
import time
from datetime import datetime
import pytz

from app.config import load_config, get_twilio_cfg
from app.data.tickers import get_all_tickers
from app.data.price_fetcher import fetch_price_data, get_current_price, get_stock_details
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

    return price_data, news_data, reddit_data


@st.cache_data(ttl=3600)
def load_fear_greed():
    return fetch_fear_greed()


def _build_stock_record(ticker: str, price_data: dict, news_data: dict, fetch_details: bool = False) -> dict | None:
    df = price_data.get(ticker)
    if df is None or len(df) < 30:
        return None
    try:
        indicators = calculate_indicators(df)
        headlines = news_data.get(ticker, [])
        sentiment = score_sentiment(headlines)
        score = calculate_score(indicators, sentiment["sentiment_score"])
        price_info = get_current_price(ticker)
        details = get_stock_details(ticker, df) if fetch_details else {}
        return {
            "ticker": ticker,
            "price": price_info["price"],
            "change_pct": price_info["change_pct"],
            "volume": price_info["volume"],
            "score": score,
            "indicators": indicators,
            "sentiment": sentiment,
            "history_df": df,
            "details": details,
            **indicators,
            "sentiment_score": sentiment["sentiment_score"],
            "sentiment_label": sentiment["sentiment_label"],
            "news_surge": sentiment["surge"],
            "ma_20": indicators.get("ma_20"),
            "week52_pct": details.get("week52_pct"),
            "atr": details.get("atr"),
            "days_to_earnings": details.get("days_to_earnings"),
            "sector": details.get("sector", "N/A"),
            "company": ticker,
        }
    except Exception:
        return None


def _render_how_to_use():
    with st.expander("❓ How to Use This App", expanded=False):
        st.markdown("""
### What is this?
This tool scans the S&P 500 and NASDAQ-100 (600+ stocks) for **swing trade opportunities** — stocks that technical indicators and news sentiment suggest may be about to move up or down in price over the next few days to weeks.

---

### Signal Score (0–100)
Every stock gets a **Signal Score** — the most important number in the app.

| Score | Color | Meaning |
|---|---|---|
| **70–100** | 🟢 Green | **BUY signal** — multiple indicators suggest the stock may rise |
| **31–69** | ⚪ Gray | **Neutral** — no clear signal, wait and watch |
| **0–30** | 🔴 Red | **SELL signal** — multiple indicators suggest the stock may fall |

---

### What the Indicators Mean

**RSI (Relative Strength Index)**
Measures if a stock is overbought or oversold.
- Below 30 = oversold (possible buy opportunity)
- Above 70 = overbought (possible sell opportunity)

**MACD**
Compares two moving averages to detect momentum shifts.
- Bullish = upward momentum building
- Bearish = downward momentum building

**MA Cross (Moving Average Crossover)**
Compares the 50-day and 200-day average prices.
- Golden Cross = 50-day crosses above 200-day (bullish long-term signal)
- Death Cross = 50-day crosses below 200-day (bearish long-term signal)

**Bollinger Bands**
Shows if a stock price is unusually high or low relative to recent history.
- Near lower band = price may be due to bounce up
- Near upper band = price may be due to pull back

**Volume Ratio**
Compares today's trading volume to the 30-day average.
- Above 1.5x = unusual activity (confirms signals)

**Sentiment**
Analyzes recent news headlines from CNBC, Reuters, MarketWatch and others.
- Positive = good news surrounding the stock
- Negative = bad news surrounding the stock

---

### My Watchlist
Your 5 personal stocks always appear at the top with detailed charts and headlines. Add them in ⚙️ Settings.

### Market Scanner Table
All 600+ stocks ranked by Signal Score. Use the filters to find:
- Only BUY signals (score ≥ 70)
- Only a specific sector
- Stocks with unusual volume

### SMS Alerts
Configure your phone number and alert thresholds in ⚙️ Settings to receive a text when any stock hits your buy or sell threshold.

### Market Mood (Sidebar)
- **CNN Fear & Greed Index**: Overall market sentiment (0 = Extreme Fear, 100 = Extreme Greed). Best buying opportunities often appear during Extreme Fear.
- **Reddit Trending**: Stocks getting unusual attention on Reddit's investing communities.

---
*Data refreshes every 15 minutes during market hours (9:30am–4:00pm ET, Mon–Fri).*
        """)


def main():
    st.title("📈 Swing Trade Scanner")
    _render_how_to_use()
    render_settings()

    if _is_market_open():
        st.success("🟢 Market Open — data refreshes every 15 minutes")
    else:
        st.warning("🔴 Market Closed — showing last session data")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div style="background:#00C853;border-radius:10px;padding:12px;text-align:center">
        <span style="font-size:24px;font-weight:bold;color:#000">70–100</span><br>
        <span style="color:#000;font-size:14px">🟢 BUY Signal — consider entering a position</span>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div style="background:#424242;border-radius:10px;padding:12px;text-align:center">
        <span style="font-size:24px;font-weight:bold;color:#fff">31–69</span><br>
        <span style="color:#fff;font-size:14px">⚪ Neutral — wait for a clearer signal</span>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div style="background:#FF1744;border-radius:10px;padding:12px;text-align:center">
        <span style="font-size:24px;font-weight:bold;color:#fff">0–30</span><br>
        <span style="color:#fff;font-size:14px">🔴 SELL Signal — consider exiting a position</span>
        </div>
        """, unsafe_allow_html=True)
    st.caption("Signal Score combines RSI, MACD, Moving Averages, Bollinger Bands, Volume, and News Sentiment into one number.")

    config = load_config()
    cache_buster = int(time.time() // _REFRESH_INTERVAL)
    watchlist_tuple = tuple(config["watchlist"])

    with st.spinner("Loading market data (this may take 30-60 seconds on first load)..."):
        price_data, news_data, reddit_data = load_all_data(watchlist_tuple, cache_buster)

    fear_greed = load_fear_greed()
    render_sidebar(fear_greed, reddit_data)

    watchlist_stocks = []
    for ticker in config["watchlist"]:
        record = _build_stock_record(ticker, price_data, news_data, fetch_details=True)
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
