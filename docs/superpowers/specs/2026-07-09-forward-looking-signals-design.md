# Forward-Looking Signal Overhaul — Design Spec
**Date:** 2026-07-09
**Status:** Approved

---

## Goal

Shift the swing trade scanner from confirming moves that already happened to detecting setups *before* a stock moves. Replace lagging indicators as the primary score drivers with leading indicators that identify coiling, accumulation, and market leadership.

---

## New Indicators

### 1. Bollinger Band Squeeze (`bb_squeeze`, `squeeze_intensity`)
- **What:** Measures current band bandwidth vs. the prior 6-month (126-day) bandwidth history
- **Calculation:** `bandwidth = (upper - lower) / middle`. Squeeze = True when current bandwidth is in the lowest 20th percentile of the last 126 days
- **Squeeze intensity:** 0–100, where 100 = tightest bandwidth in 6 months
- **Outputs:** `bb_squeeze: bool`, `squeeze_intensity: int (0–100)`

### 2. OBV Trend (`obv_trend`)
- **What:** On-Balance Volume — adds volume on up days, subtracts on down days. Rising OBV with flat/falling price = institutional accumulation
- **Calculation:** Cumulative OBV series. Compare 10-day EMA of OBV slope to zero
  - `accumulating` = OBV slope positive while price change over 10 days < +2%
  - `distributing` = OBV slope negative while price change over 10 days > -2%
  - `neutral` = everything else
- **Output:** `obv_trend: str ("accumulating" | "distributing" | "neutral")`

### 3. Relative Strength vs SPY (`rs_vs_spy`)
- **What:** Stock's 20-day return minus SPY's 20-day return
- **Calculation:** `rs = (stock_close[-1]/stock_close[-20] - 1) - (spy_close[-1]/spy_close[-20] - 1)`, expressed as percentage points
- **Data:** SPY fetched once per cache cycle alongside all other tickers; reused for all stocks
- **Output:** `rs_vs_spy: float` (e.g., +6.2 means 6.2% stronger than market over 20 days)

### 4. Consolidation Score (`consolidation`)
- **What:** How tight has the price range been over the last 15 days vs. the prior 30 days
- **Calculation:** `recent_range = (high[-15:].max() - low[-15:].min()) / close[-15:].mean()`. Compare to `prior_range` over days -45 to -15
  - `tight` = recent range < 50% of prior range
  - `wide` = recent range > 150% of prior range
  - `normal` = everything else
- **Output:** `consolidation: str ("tight" | "normal" | "wide")`

### 5. Short Interest (`short_pct`, `short_ratio`)
- **What:** Percentage of float sold short; days-to-cover ratio
- **Data source:** `yf.Ticker(ticker).info` fields `shortPercentOfFloat` and `shortRatio`
- **Performance:** Only fetched for watchlist stocks (via existing `get_stock_details`) and top 50 Early Signals candidates. Not fetched for all 600+ stocks
- **Output:** `short_pct: float | None`, `short_ratio: float | None`

---

## Signal Score Reweighting

### Removed from score
- MA Cross (golden/death cross) — too lagging; kept as display-only in watchlist and scanner
- Bollinger position (upper/mid/lower) — replaced by BB Squeeze

### New weights
| Indicator | Weight | Type |
|-----------|--------|------|
| BB Squeeze | 20% | Leading |
| OBV Trend | 18% | Leading |
| Relative Strength vs SPY | 17% | Leading |
| Consolidation | 10% | Leading |
| Volume Surge | 10% | Leading |
| RSI | 10% | Mixed |
| MACD | 8% | Lagging (reduced, kept) |
| Support/Resistance | 7% | Leading |
| News Sentiment | +bonus up to 10pts | Leading |

### Score normalization
Same 0–100 scale. Same green/gray/red thresholds (70+, 31–69, 0–30). Label changes from "Score" to "Setup Score" throughout the UI.

---

## Data Pipeline Changes

### `app/data/price_fetcher.py`
- Fetch SPY in the bulk `fetch_price_data()` call alongside all tickers
- Return SPY DataFrame separately so scorer can reference it without an extra API call

### `app/signals/indicators.py`
- Add: `_bb_squeeze()`, `_obv_trend()`, `_relative_strength()`, `_consolidation()`
- `calculate_indicators(df, spy_df)` — add `spy_df` parameter
- Remove: `_bollinger_position()` (replaced by squeeze)
- Keep: `_support_resistance()`, `_volume_metrics()`, `_rsi()`, `_macd_signal()`, `_ma_cross()` (display only)

### `app/signals/scorer.py`
- Replace `_WEIGHTS` dict with new weights above
- Remove MA cross and bollinger position from score calculation
- Add OBV, RS, consolidation, squeeze to score

### `app/data/price_fetcher.py`
- `get_stock_details()` adds `short_pct` and `short_ratio` from `yf.Ticker().info`

---

## UI Changes

### `app/ui/scanner.py`
- Add columns: `BB Squeeze`, `OBV`, `RS vs SPY`
- Rename "Score" column header to "Setup Score"
- Default sort: Setup Score descending
- Add 🔥 badge to ticker cell when `bb_squeeze=True`

### New: `app/ui/early_signals.py`
- Filters stocks where: `bb_squeeze=True` AND `obv_trend="accumulating"` AND `rs_vs_spy > 0`
- Fetches `short_pct`/`short_ratio` for matching stocks (capped at 50)
- Summary line at top: *"N stocks are coiling with institutional accumulation and outperforming the market today."*
- Table columns: Ticker | Price | Setup Score | Squeeze Intensity | OBV Signal | RS vs SPY | Short % | Sector
- Empty state: *"No stocks meeting all three criteria right now. Check back during the trading day."*

### `main.py`
- Wrap scanner + early signals in `st.tabs(["📊 Market Scanner", "🔥 Early Signals"])`
- Pass `spy_df` from `load_all_data()` into `_build_stock_record()`

### `app/ui/watchlist.py`
- Add "Setup Status" line below verdict box:
  - 🔥 Squeeze building — breakout may be near
  - 📈 Accumulating — volume rising quietly
  - 💤 No setup — waiting for conditions

### `app/ui/sidebar.py`
- Update "How It Works" explainer to describe new leading-indicator approach

---

## Files Changed
- `app/signals/indicators.py` — add 4 new indicator functions, update `calculate_indicators` signature
- `app/signals/scorer.py` — new weights, remove 2 old signals
- `app/data/price_fetcher.py` — add SPY to bulk fetch, add short interest to `get_stock_details`
- `app/ui/scanner.py` — new columns, rename score header, squeeze badge
- `app/ui/early_signals.py` — new file
- `app/ui/watchlist.py` — setup status line
- `main.py` — tabs, pass spy_df

## Files NOT Changed
- `app/data/stocktwits_fetcher.py`
- `app/data/fear_greed.py`
- `app/data/news_fetcher.py`
- `app/alerts/`
- `app/config.py`
- `app/ui/sidebar.py`
- `app/ui/settings.py`
