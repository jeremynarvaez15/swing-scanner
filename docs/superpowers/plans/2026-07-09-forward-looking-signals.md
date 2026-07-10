# Forward-Looking Signal Overhaul — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace lagging indicators as the primary score drivers with five leading indicators (BB Squeeze, OBV Trend, Relative Strength vs SPY, Consolidation, Short Interest), reweight the signal scorer, add an Early Signals tab, and surface setup status on watchlist cards.

**Architecture:** All new signals are computed from existing OHLCV data already fetched by yfinance — no new APIs. SPY is added to the bulk price fetch and reused across all 600+ stocks. Short interest is fetched individually only for watchlist + top Early Signals candidates to stay within API limits.

**Tech Stack:** Python 3.11, pandas, numpy, yfinance, Streamlit

## Global Constraints
- Python 3.11
- All indicator functions return plain Python scalars (int, float, str, bool) — no pandas Series
- `calculate_indicators(df, spy_df)` — `spy_df` is a pandas DataFrame with a `Close` column; callers pass it in; never fetch SPY inside indicators.py
- Score remains 0–100 int; thresholds 70+ = buy, 30- = sell unchanged
- Do not change any files in `app/alerts/`, `app/config.py`, `app/data/stocktwits_fetcher.py`, `app/data/fear_greed.py`, `app/data/news_fetcher.py`, `app/ui/sidebar.py`, `app/ui/settings.py`
- All git commits use present-tense imperative messages

---

## File Map

| File | Action | Responsibility |
|------|--------|----------------|
| `app/data/price_fetcher.py` | Modify | Add SPY to bulk fetch; add short interest to `get_stock_details` |
| `app/signals/indicators.py` | Modify | Add 4 new indicator functions; update `calculate_indicators` signature |
| `app/signals/scorer.py` | Modify | New weights; remove bb_position and ma_cross from score |
| `app/ui/early_signals.py` | Create | Early Signals tab UI |
| `app/ui/scanner.py` | Modify | New columns; rename score header; squeeze badge |
| `app/ui/watchlist.py` | Modify | Setup status line below verdict box |
| `main.py` | Modify | Pass spy_df through pipeline; wrap scanner+early_signals in tabs |

---

## Task 1: Add SPY to bulk price fetch + short interest to stock details

**Files:**
- Modify: `app/data/price_fetcher.py`

**Interfaces:**
- Produces: `fetch_price_data(tickers)` now also returns `spy_df: pd.DataFrame` as a second return value — tuple `(dict[str, pd.DataFrame], pd.DataFrame)`
- Produces: `get_stock_details(ticker, df)` now also returns `short_pct: float | None` and `short_ratio: float | None`

- [ ] **Step 1: Update `fetch_price_data` to also download SPY and return it**

Replace the entire `fetch_price_data` function in `app/data/price_fetcher.py`:

```python
def fetch_price_data(tickers: list[str]) -> tuple[dict[str, pd.DataFrame], pd.DataFrame]:
    """
    Download 1 year of daily OHLCV for all tickers + SPY in one API call.
    Returns (dict keyed by ticker symbol, spy_df).
    SPY is excluded from the result dict but returned separately for RS calculation.
    """
    all_symbols = list(set(tickers) | {"SPY"})
    raw = yf.download(
        tickers=all_symbols,
        period="1y",
        interval="1d",
        group_by="ticker",
        auto_adjust=True,
        threads=True,
        progress=False,
    )

    result = {}
    spy_df = pd.DataFrame()

    if len(all_symbols) == 1:
        # Only happens if tickers=["SPY"]
        df = raw[["Open", "High", "Low", "Close", "Volume"]].copy()
        df.dropna(inplace=True)
        spy_df = df
    else:
        for ticker in all_symbols:
            try:
                df = raw[ticker][["Open", "High", "Low", "Close", "Volume"]].copy()
                df.dropna(inplace=True)
                if len(df) == 0:
                    continue
                if ticker == "SPY":
                    spy_df = df
                else:
                    result[ticker] = df
            except KeyError:
                continue

    return result, spy_df
```

- [ ] **Step 2: Add short interest fields to `get_stock_details`**

In `app/data/price_fetcher.py`, update the `details` dict initializer and the `yf.Ticker` block inside `get_stock_details`:

Replace the `details = { ... }` initializer:
```python
    details = {
        "atr": None,
        "week52_pct": None,
        "week52_low": None,
        "week52_high": None,
        "days_to_earnings": None,
        "sector": "N/A",
        "target_up": None,
        "target_down": None,
        "short_pct": None,
        "short_ratio": None,
    }
```

Inside the `try` block that calls `yf.Ticker(ticker)`, after `details["sector"] = info.get("sector", "N/A")` add:
```python
        raw_short_pct = info.get("shortPercentOfFloat")
        if raw_short_pct is not None:
            details["short_pct"] = round(float(raw_short_pct) * 100, 1)
        raw_short_ratio = info.get("shortRatio")
        if raw_short_ratio is not None:
            details["short_ratio"] = round(float(raw_short_ratio), 1)
```

- [ ] **Step 3: Commit**

```bash
git add app/data/price_fetcher.py
git commit -m "feat: add SPY to bulk fetch and short interest to stock details"
```

---

## Task 2: Add four new leading indicator functions

**Files:**
- Modify: `app/signals/indicators.py`

**Interfaces:**
- Consumes: `df` with columns `Open`, `High`, `Low`, `Close`, `Volume`; `spy_df` with column `Close`
- Produces: `calculate_indicators(df, spy_df)` returns dict with all existing keys PLUS:
  - `bb_squeeze: bool`
  - `squeeze_intensity: int` (0–100)
  - `obv_trend: str` ("accumulating" | "distributing" | "neutral")
  - `rs_vs_spy: float` (percentage points, e.g. 6.2)
  - `consolidation: str` ("tight" | "normal" | "wide")
  - existing keys kept: `rsi`, `macd_signal`, `ma_cross`, `ma_20`, `ma_50`, `ma_200`, `bb_position`, `volume_surge`, `volume_ratio`, `near_support`, `near_resistance`

- [ ] **Step 1: Add `_bb_squeeze` function**

Add after the existing `_bollinger_position` function in `app/signals/indicators.py`:

```python
def _bb_squeeze(close: pd.Series, period: int = 20, lookback: int = 126) -> tuple[bool, int]:
    """
    Detect Bollinger Band squeeze: bandwidth at a 6-month low signals coiling.
    Returns (squeeze: bool, intensity: int 0-100 where 100=tightest ever).
    """
    rolling_mean = close.rolling(period).mean()
    rolling_std = close.rolling(period).std()
    upper = rolling_mean + 2 * rolling_std
    lower = rolling_mean - 2 * rolling_std
    bandwidth = (upper - lower) / rolling_mean.replace(0, float("nan"))
    current_bw = bandwidth.iloc[-1]
    history = bandwidth.dropna().iloc[-lookback:]
    if len(history) < 20 or pd.isna(current_bw):
        return False, 0
    pct_rank = float((history < current_bw).sum()) / len(history)
    squeeze = pct_rank <= 0.20
    intensity = int((1 - pct_rank) * 100)
    return squeeze, intensity
```

- [ ] **Step 2: Add `_obv_trend` function**

Add after `_bb_squeeze`:

```python
def _obv_trend(close: pd.Series, volume: pd.Series, price_window: int = 10) -> str:
    """
    On-Balance Volume trend: rising OBV with flat/falling price = accumulation.
    """
    direction = close.diff().apply(lambda x: 1 if x > 0 else (-1 if x < 0 else 0))
    obv = (direction * volume).cumsum()
    if len(obv) < price_window + 2:
        return "neutral"
    obv_slope = obv.ewm(span=price_window, adjust=False).mean()
    slope_now = float(obv_slope.iloc[-1]) - float(obv_slope.iloc[-price_window])
    price_chg = (float(close.iloc[-1]) - float(close.iloc[-price_window])) / float(close.iloc[-price_window]) * 100
    if slope_now > 0 and price_chg < 2.0:
        return "accumulating"
    if slope_now < 0 and price_chg > -2.0:
        return "distributing"
    return "neutral"
```

- [ ] **Step 3: Add `_relative_strength` function**

Add after `_obv_trend`:

```python
def _relative_strength(close: pd.Series, spy_close: pd.Series, window: int = 20) -> float:
    """
    Stock's 20-day return minus SPY's 20-day return, in percentage points.
    Positive = stock outperforming the market (leadership signal).
    """
    if len(close) < window + 1 or len(spy_close) < window + 1:
        return 0.0
    stock_return = (float(close.iloc[-1]) / float(close.iloc[-window]) - 1) * 100
    spy_return = (float(spy_close.iloc[-1]) / float(spy_close.iloc[-window]) - 1) * 100
    return round(stock_return - spy_return, 2)
```

- [ ] **Step 4: Add `_consolidation` function**

Add after `_relative_strength`:

```python
def _consolidation(high: pd.Series, low: pd.Series, close: pd.Series,
                   recent: int = 15, prior: int = 30) -> str:
    """
    Compare recent price range to prior range.
    Tight = stock coiling; wide = volatile/extended.
    """
    if len(close) < recent + prior:
        return "normal"
    recent_range = (float(high.iloc[-recent:].max()) - float(low.iloc[-recent:].min()))
    recent_mid = float(close.iloc[-recent:].mean())
    prior_range = (float(high.iloc[-(recent + prior):-recent].max()) -
                   float(low.iloc[-(recent + prior):-recent].min()))
    if recent_mid == 0 or prior_range == 0:
        return "normal"
    ratio = (recent_range / recent_mid) / (prior_range / recent_mid)
    if ratio < 0.50:
        return "tight"
    if ratio > 1.50:
        return "wide"
    return "normal"
```

- [ ] **Step 5: Update `calculate_indicators` signature and body**

Replace the entire `calculate_indicators` function:

```python
def calculate_indicators(df: pd.DataFrame, spy_df: pd.DataFrame | None = None) -> dict:
    """Calculate all swing trade indicators from OHLCV DataFrame."""
    close = df["Close"]
    volume = df["Volume"]
    high = df["High"]
    low = df["Low"]

    rsi = _rsi(close)
    macd_signal = _macd_signal(close)
    ma_cross, ma_50, ma_200 = _ma_cross(close)
    bb_position = _bollinger_position(close)
    volume_surge, volume_ratio = _volume_metrics(volume)
    near_support, near_resistance = _support_resistance(close)
    ma_20 = round(float(close.rolling(20).mean().iloc[-1]), 2) if len(close) >= 20 else round(float(close.mean()), 2)
    bb_squeeze, squeeze_intensity = _bb_squeeze(close)
    obv_trend = _obv_trend(close, volume)
    consolidation = _consolidation(high, low, close)

    spy_close = spy_df["Close"] if spy_df is not None and not spy_df.empty else pd.Series(dtype=float)
    rs_vs_spy = _relative_strength(close, spy_close)

    return {
        "rsi": rsi,
        "macd_signal": macd_signal,
        "ma_cross": ma_cross,
        "ma_20": ma_20,
        "ma_50": ma_50,
        "ma_200": ma_200,
        "bb_position": bb_position,
        "volume_surge": volume_surge,
        "volume_ratio": volume_ratio,
        "near_support": near_support,
        "near_resistance": near_resistance,
        "bb_squeeze": bb_squeeze,
        "squeeze_intensity": squeeze_intensity,
        "obv_trend": obv_trend,
        "rs_vs_spy": rs_vs_spy,
        "consolidation": consolidation,
    }
```

- [ ] **Step 6: Commit**

```bash
git add app/signals/indicators.py
git commit -m "feat: add BB squeeze, OBV trend, relative strength, consolidation indicators"
```

---

## Task 3: Reweight signal scorer

**Files:**
- Modify: `app/signals/scorer.py`

**Interfaces:**
- Consumes: `indicators` dict (now includes `bb_squeeze`, `squeeze_intensity`, `obv_trend`, `rs_vs_spy`, `consolidation`)
- Produces: `calculate_score(indicators, sentiment_score) -> int` (unchanged signature)

- [ ] **Step 1: Replace scorer with new leading-first weights**

Replace the entire contents of `app/signals/scorer.py`:

```python
_WEIGHTS = {
    "bb_squeeze": 0.20,
    "obv_trend": 0.18,
    "rs_vs_spy": 0.17,
    "consolidation": 0.10,
    "volume": 0.10,
    "rsi": 0.10,
    "macd": 0.08,
    "support_resistance": 0.07,
}
_SENTIMENT_BONUS_MAX = 10.0


def calculate_score(indicators: dict, sentiment_score: float) -> int:
    """
    Compute composite setup score 0-100. Leading indicators weighted first.
    sentiment_score: float from -1.0 (very negative) to 1.0 (very positive).
    """
    raw = 0.0

    # BB Squeeze (leading): squeeze + intensity boost
    if indicators.get("bb_squeeze"):
        intensity = indicators.get("squeeze_intensity", 50)
        squeeze_raw = 0.5 + (intensity / 200.0)  # 0.5 to 1.0
    else:
        squeeze_raw = 0.0
    raw += squeeze_raw * _WEIGHTS["bb_squeeze"]

    # OBV Trend (leading)
    obv_map = {"accumulating": 1.0, "neutral": 0.0, "distributing": -1.0}
    raw += obv_map.get(indicators.get("obv_trend", "neutral"), 0.0) * _WEIGHTS["obv_trend"]

    # Relative Strength vs SPY (leading): clamp to -15/+15 range
    rs = float(indicators.get("rs_vs_spy", 0.0))
    rs_raw = max(-1.0, min(1.0, rs / 15.0))
    raw += rs_raw * _WEIGHTS["rs_vs_spy"]

    # Consolidation (leading)
    consol_map = {"tight": 1.0, "normal": 0.0, "wide": -0.5}
    raw += consol_map.get(indicators.get("consolidation", "normal"), 0.0) * _WEIGHTS["consolidation"]

    # Volume surge (leading)
    raw += (0.5 if indicators.get("volume_surge") else 0.0) * _WEIGHTS["volume"]

    # RSI (mixed)
    rsi = indicators.get("rsi", 50)
    if rsi <= 30:
        rsi_raw = 1.0
    elif rsi >= 70:
        rsi_raw = -1.0
    else:
        rsi_raw = -((rsi - 50) / 20)
    raw += rsi_raw * _WEIGHTS["rsi"]

    # MACD (lagging, reduced)
    macd_map = {"bullish": 1.0, "neutral": 0.0, "bearish": -1.0}
    raw += macd_map.get(indicators.get("macd_signal", "neutral"), 0.0) * _WEIGHTS["macd"]

    # Support/Resistance (leading)
    sr_raw = 0.0
    if indicators.get("near_support"):
        sr_raw += 1.0
    if indicators.get("near_resistance"):
        sr_raw -= 1.0
    raw += sr_raw * _WEIGHTS["support_resistance"]

    # Normalize raw (-1 to 1) → base score (0 to 100)
    # raw theoretical range: sum of all weights = 1.0, so raw in [-1, 1]
    base_score = (raw + 1.0) / 2.0 * 100.0

    # Sentiment bonus: up to +/- 10 points
    sentiment_adj = float(sentiment_score) * _SENTIMENT_BONUS_MAX
    final = base_score + sentiment_adj

    return int(max(0, min(100, round(final))))
```

- [ ] **Step 2: Commit**

```bash
git add app/signals/scorer.py
git commit -m "feat: reweight scorer with leading indicators first"
```

---

## Task 4: Update main.py data pipeline

**Files:**
- Modify: `main.py`

**Interfaces:**
- Consumes: `fetch_price_data` now returns `(dict, spy_df)`
- Consumes: `calculate_indicators(df, spy_df)` takes spy_df
- Produces: `_build_stock_record` passes spy_df to indicators; stock record gains `bb_squeeze`, `squeeze_intensity`, `obv_trend`, `rs_vs_spy`, `consolidation` keys
- Produces: `load_all_data` returns `(price_data, news_data, stocktwits_data, spy_df)` — 4-tuple

- [ ] **Step 1: Update `load_all_data` to unpack spy_df and return it**

In `main.py`, replace the `load_all_data` function:

```python
@st.cache_data(ttl=_REFRESH_INTERVAL)
def load_all_data(watchlist: tuple, _cache_buster: int):
    all_tickers = get_all_tickers()
    price_data, spy_df = fetch_price_data(list(all_tickers))

    news_api_key = st.secrets.get("NEWS_API_KEY", "")
    news_data = fetch_news(list(watchlist), news_api_key) if news_api_key else {}

    stocktwits_data = []
    try:
        stocktwits_data = fetch_stocktwits_trending()
    except Exception:
        pass

    return price_data, news_data, stocktwits_data, spy_df
```

- [ ] **Step 2: Update `_build_stock_record` to accept and pass spy_df**

Replace `_build_stock_record`:

```python
def _build_stock_record(ticker: str, price_data: dict, news_data: dict,
                         spy_df=None, fetch_details: bool = False) -> dict | None:
    df = price_data.get(ticker)
    if df is None or len(df) < 30:
        return None
    try:
        indicators = calculate_indicators(df, spy_df)
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
            "short_pct": details.get("short_pct"),
            "short_ratio": details.get("short_ratio"),
        }
    except Exception:
        return None
```

- [ ] **Step 3: Update main() to unpack 4-tuple and pass spy_df**

In `main()`, replace:
```python
        price_data, news_data, stocktwits_data = load_all_data(watchlist_tuple, cache_buster)
```
with:
```python
        price_data, news_data, stocktwits_data, spy_df = load_all_data(watchlist_tuple, cache_buster)
```

Replace the watchlist loop:
```python
    watchlist_stocks = []
    for ticker in config["watchlist"]:
        record = _build_stock_record(ticker, price_data, news_data, spy_df=spy_df, fetch_details=True)
        if record:
            watchlist_stocks.append(record)
```

Replace the scanner loop:
```python
    scan_results = []
    all_tickers = list(price_data.keys())
    progress = st.progress(0, text="Building signal scores...")
    for i, ticker in enumerate(all_tickers):
        record = _build_stock_record(ticker, price_data, news_data, spy_df=spy_df)
        if record:
            scan_results.append(record)
        if (i + 1) % 10 == 0:
            progress.progress((i + 1) / len(all_tickers))
    progress.empty()
```

- [ ] **Step 4: Wrap scanner and early signals in tabs**

In `main()`, replace:
```python
    render_scanner(scan_results)
```
with:
```python
    tab1, tab2 = st.tabs(["📊 Market Scanner", "🔥 Early Signals"])
    with tab1:
        render_scanner(scan_results)
    with tab2:
        from app.ui.early_signals import render_early_signals
        render_early_signals(scan_results)
```

- [ ] **Step 5: Update the How To Use text**

In `_render_how_to_use()`, replace:
```python
### Market Mood (Sidebar)
- **CNN Fear & Greed Index**: Overall market sentiment (0 = Extreme Fear, 100 = Extreme Greed). Best buying opportunities often appear during Extreme Fear.
- **Reddit Trending**: Stocks getting unusual attention on Reddit's investing communities.
```
with:
```python
### Market Mood (Sidebar)
- **Fear & Greed Index**: Overall market sentiment (0 = Extreme Fear, 100 = Extreme Greed). Best buying opportunities often appear during Extreme Fear.
- **StockTwits Trending**: Stocks being most watched and discussed by active traders right now, with bullish/bearish sentiment.

### Early Signals Tab
Stocks that are simultaneously **coiling** (Bollinger squeeze), **accumulating** (OBV rising), and **leading the market** (outperforming SPY). This is your daily shortlist of potential breakout candidates.
```

- [ ] **Step 6: Commit**

```bash
git add main.py
git commit -m "feat: wire spy_df through pipeline and add Early Signals tab"
```

---

## Task 5: Create Early Signals tab UI

**Files:**
- Create: `app/ui/early_signals.py`

**Interfaces:**
- Consumes: `scan_results: list[dict]` — each dict has keys from `_build_stock_record` including `bb_squeeze`, `obv_trend`, `rs_vs_spy`, `squeeze_intensity`, `consolidation`, `short_pct`, `score`, `ticker`, `price`, `sector`
- Produces: `render_early_signals(scan_results: list[dict]) -> None`

- [ ] **Step 1: Create `app/ui/early_signals.py`**

```python
import streamlit as st
import pandas as pd


def render_early_signals(scan_results: list[dict]):
    st.subheader("🔥 Early Signals — Stocks Setting Up Before the Move")
    st.caption(
        "These stocks are simultaneously **coiling** (Bollinger squeeze), "
        "**accumulating** (smart money buying quietly), and **leading the market** "
        "(outperforming S&P 500). This is your daily shortlist of potential breakout candidates."
    )

    candidates = [
        r for r in scan_results
        if r.get("bb_squeeze") and
           r.get("obv_trend") == "accumulating" and
           (r.get("rs_vs_spy") or 0) > 0
    ]

    if not candidates:
        st.info(
            "No stocks meet all three criteria right now (squeeze + accumulation + market leadership). "
            "This list is intentionally strict — check back during the trading day or after a market pullback."
        )
        return

    candidates.sort(key=lambda r: r.get("score", 0), reverse=True)

    st.success(
        f"**{len(candidates)} stock{'s' if len(candidates) != 1 else ''} "
        f"coiling with institutional accumulation and outperforming the market today.**"
    )

    rows = []
    for r in candidates[:50]:
        squeeze_int = r.get("squeeze_intensity", 0)
        squeeze_bar = "🔥" * min(5, max(1, squeeze_int // 20))
        obv = r.get("obv_trend", "neutral").capitalize()
        rs = r.get("rs_vs_spy", 0.0)
        rs_str = f"+{rs:.1f}%" if rs >= 0 else f"{rs:.1f}%"
        short_pct = r.get("short_pct")
        short_str = f"{short_pct:.1f}%" if short_pct is not None else "—"
        consol = r.get("consolidation", "normal").capitalize()
        rows.append({
            "Ticker": f"${r['ticker']}",
            "Price": f"${r['price']:.2f}",
            "Setup Score": r.get("score", 0),
            "Squeeze": squeeze_bar,
            "Intensity": squeeze_int,
            "OBV Signal": obv,
            "RS vs SPY": rs_str,
            "Consolidation": consol,
            "Short %": short_str,
            "Sector": r.get("sector", "N/A"),
        })

    df = pd.DataFrame(rows)
    col_config = {
        "Setup Score": st.column_config.ProgressColumn(
            "Setup Score", min_value=0, max_value=100, format="%d"
        ),
        "Intensity": st.column_config.ProgressColumn(
            "Squeeze Intensity", min_value=0, max_value=100, format="%d%%"
        ),
    }
    st.dataframe(df, use_container_width=True, hide_index=True, column_config=col_config)

    with st.expander("❓ How to read this table"):
        st.markdown("""
**Setup Score** — the new forward-looking signal score (0–100). Higher = stronger setup.

**Squeeze** — 🔥 icons show how tight the Bollinger Bands are. More 🔥 = more compressed = bigger potential move when it breaks out.

**Squeeze Intensity** — 0–100. A score of 90 means the bands are tighter than 90% of the last 6 months.

**OBV Signal** — On-Balance Volume. "Accumulating" means volume is flowing in quietly while the price is still flat. Institutions buy before retail notices.

**RS vs SPY** — How much better (or worse) the stock is doing vs. the S&P 500 over the last 20 days. Positive = the stock is leading the market.

**Consolidation** — "Tight" means the stock has been trading in a narrow range — like a coiled spring.

**Short %** — How many shares are being shorted. High short interest + a breakout = potential short squeeze, which accelerates the move up.

*These stocks are setups, not guarantees. Always use a stop-loss and manage your position size.*
        """)
```

- [ ] **Step 2: Commit**

```bash
git add app/ui/early_signals.py
git commit -m "feat: add Early Signals tab UI"
```

---

## Task 6: Update Market Scanner table

**Files:**
- Modify: `app/ui/scanner.py`

**Interfaces:**
- Consumes: `scan_results` list with new keys: `bb_squeeze`, `squeeze_intensity`, `obv_trend`, `rs_vs_spy`

- [ ] **Step 1: Add new columns and rename score header**

Replace the entire `display_cols` dict and the column-formatting block in `render_scanner`:

```python
    display_cols = {
        "Ticker": "Ticker",
        "price": "Price",
        "change_pct": "Day %",
        "score": "Setup Score",
        "bb_squeeze": "Squeeze",
        "obv_trend": "OBV",
        "rs_vs_spy": "RS vs SPY",
        "rsi": "RSI",
        "macd_signal": "MACD",
        "ma_20": "MA20",
        "ma_50": "MA50",
        "ma_200": "MA200",
        "volume_ratio": "Vol Ratio",
        "week52_pct": "52W Position",
        "days_to_earnings": "Earnings",
        "sentiment_label": "Sentiment",
        "sector": "Sector",
    }
```

After the `display_df = display_df.rename(...)` line, add formatting for new columns:

```python
    if "Squeeze" in display_df.columns:
        display_df["Squeeze"] = display_df["Squeeze"].apply(
            lambda x: "🔥 Yes" if x else "—"
        )
    if "OBV" in display_df.columns:
        display_df["OBV"] = display_df["OBV"].apply(
            lambda x: {"accumulating": "📈 Accum.", "distributing": "📉 Dist.", "neutral": "—"}.get(str(x), "—")
        )
    if "RS vs SPY" in display_df.columns:
        display_df["RS vs SPY"] = display_df["RS vs SPY"].apply(
            lambda x: f"+{x:.1f}%" if pd.notna(x) and x >= 0 else (f"{x:.1f}%" if pd.notna(x) else "—")
        )
```

Also update the `col_config` block to rename "Score" → "Setup Score":

```python
    col_config = {}
    if "Setup Score" in display_df.columns:
        col_config["Setup Score"] = st.column_config.ProgressColumn(
            "Setup Score", min_value=0, max_value=100, format="%d"
        )
```

- [ ] **Step 2: Commit**

```bash
git add app/ui/scanner.py
git commit -m "feat: add squeeze/OBV/RS columns to scanner, rename score header"
```

---

## Task 7: Add Setup Status to watchlist cards

**Files:**
- Modify: `app/ui/watchlist.py`

**Interfaces:**
- Consumes: `stock["indicators"]` dict — gains `bb_squeeze`, `obv_trend`, `consolidation` keys

- [ ] **Step 1: Add `_setup_status` helper and render it below verdict box**

Add this function after `_verdict` in `app/ui/watchlist.py`:

```python
def _setup_status(indicators: dict) -> tuple[str, str, str]:
    """Return (emoji, label, color) for setup status line."""
    squeeze = indicators.get("bb_squeeze", False)
    obv = indicators.get("obv_trend", "neutral")
    consol = indicators.get("consolidation", "normal")
    if squeeze and obv == "accumulating":
        return "🔥", "Squeeze building — breakout may be near", "#FF8800"
    if obv == "accumulating" and consol == "tight":
        return "📈", "Accumulating — volume rising quietly", "#00C853"
    if squeeze:
        return "🔥", "Coiling — watch for a breakout", "#FF8800"
    return "💤", "No setup yet — waiting for conditions", "#9E9E9E"
```

In `render_watchlist`, after the verdict box `st.markdown(...)` block and before the earnings warning, add:

```python
            # --- Setup Status ---
            setup_emoji, setup_label, setup_color = _setup_status(indicators)
            st.markdown(
                f'<div style="font-size:12px;margin:4px 0;padding:4px 8px;'
                f'background:{setup_color}22;border-radius:6px;'
                f'border-left:3px solid {setup_color}">'
                f'{setup_emoji} <span style="color:{setup_color}">{setup_label}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
```

- [ ] **Step 2: Commit**

```bash
git add app/ui/watchlist.py
git commit -m "feat: add setup status line to watchlist cards"
```

---

## Task 8: Push to GitHub and verify deploy

- [ ] **Step 1: Push all commits**

```bash
git push origin main
```

- [ ] **Step 2: Verify on Streamlit Cloud**

Open https://swing-scanner-zstwwwy3xk3duafbpejnfl.streamlit.app and confirm:
- The app loads without an import error
- The "🔥 Early Signals" tab appears next to "📊 Market Scanner"
- Watchlist cards show a Setup Status line (🔥, 📈, or 💤)
- Scanner table has "Setup Score", "Squeeze", "OBV", and "RS vs SPY" columns
- No "reddit_fetcher" import errors in the Streamlit logs

- [ ] **Step 3: Update progress ledger**

Append to `docs/superpowers/plans/sdd-progress.md`:
```
## 2026-07-09 — Forward-Looking Signal Overhaul
- Added BB Squeeze, OBV Trend, RS vs SPY, Consolidation indicators
- Reweighted scorer to favor leading indicators (65% leading, 25% mixed/lagging, 10% sentiment bonus)
- Added Early Signals tab with strict 3-criteria filter
- Added Setup Status line to watchlist cards
- Scanner renamed "Score" → "Setup Score"; added Squeeze/OBV/RS columns
```

```bash
git add docs/superpowers/plans/sdd-progress.md
git commit -m "docs: update progress ledger for forward-looking overhaul"
git push origin main
```
