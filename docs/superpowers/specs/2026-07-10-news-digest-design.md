# News Digest Tab — Design Spec
**Date:** 2026-07-10
**Status:** Approved

---

## Goal

Add a "📰 News Digest" tab to the existing swing trade scanner that aggregates financial news, summarizes it with AI, ranks stories by market impact, and surfaces a dedicated AI/chip trade feed — so the user can stay fully informed in minutes instead of hours.

---

## Scope

- New tab inside the existing Streamlit app (no new deployment)
- Covers S&P 100 + CIFR (Cipher Digital)
- Refreshes every 60 minutes (cached to control API costs)
- Requires two API keys: existing NewsAPI key + new Anthropic API key

---

## News Sources

Uses existing `NEWS_API_KEY` (already in Streamlit secrets). Three query categories:

### Global Business & World Events
Terms: `"Federal Reserve"`, `"interest rates"`, `"inflation"`, `"recession"`, `"GDP"`, `"tariffs"`, `"China economy"`, `"oil prices"`, `"geopolitical"`, `"earnings season"`, `"S&P 500"`, `"stock market"`, `"Treasury"`, `"debt"`, `"jobs report"`

### AI Trade
Terms: `"artificial intelligence"`, `"NVIDIA"`, `"semiconductors"`, `"Blackwell"`, `"data center"`, `"AI chips"`, `"Broadcom"`, `"AVGO"`, `"AMD chips"`, `"Microsoft AI"`, `"Google AI"`, `"Meta AI"`, `"AI spending"`, `"GPU"`

### Company-Specific
One query per S&P 100 company (ticker + company name). CIFR queried as `"Cipher Digital"` and `"CIFR"`.

---

## AI Processing (Anthropic API)

Key: `ANTHROPIC_API_KEY` stored in `.streamlit/secrets.toml`.
Model: `claude-haiku-4-5-20251001` (fastest + cheapest, sufficient for summarization).

For each article, the Claude API returns a JSON object:

```json
{
  "summary": "2-3 sentence plain-English summary focused on investor impact",
  "impact_score": 7,
  "impact_direction": "bearish",
  "ai_trade_tag": true
}
```

**impact_score:** 1–10 integer
- 9–10: Market-moving (Fed decision, major geopolitical event, mega-cap earnings miss)
- 7–8: Significant (sector rotation, major company news, macro data release)
- 5–6: Notable (industry trends, analyst upgrades/downgrades)
- 3–4: Informational (company updates, minor macro data)
- 1–2: Background noise (minor industry news)

**impact_direction:** `"bullish"` | `"bearish"` | `"neutral"` — overall effect on US equities

**ai_trade_tag:** `true` if story is relevant to AI infrastructure, chips, cloud, or AI model development

### Caching
- All summaries cached with `@st.cache_data(ttl=3600)` — 1 hour
- Claude API only called on cache miss (once per hour maximum)
- Estimated cost: ~$1–2/month at normal usage

### Prompt template
```
You are a financial analyst. Summarize this news article for a retail swing trader.

Headline: {title}
Content: {description or first 500 chars of content}

Return ONLY valid JSON with these exact keys:
- summary: 2-3 sentences explaining what happened and why it matters to stock investors
- impact_score: integer 1-10 (10 = major market-moving event)
- impact_direction: one of "bullish", "bearish", "neutral" for US equities overall
- ai_trade_tag: true if this story is about AI, semiconductors, data centers, or AI model development; false otherwise
```

---

## Page Layout

### Tab: 📰 News Digest

#### Section 1: 🌍 Market Intelligence Feed

- Subheader: "🌍 Market Intelligence Feed"
- Caption: "Global business, world events, and market news — ranked by impact"
- Shows ALL fetched articles sorted by `impact_score` descending
- Each article displayed as a card:

```
[8] 🔴  Fed signals rates staying higher longer
        The Federal Reserve indicated it will hold rates above 5% through
        year-end, citing persistent inflation in services. This is bearish
        for rate-sensitive sectors like real estate and utilities, and may
        pressure growth stocks that rely on cheap capital.
        Reuters · 2 hours ago · [Read Full Article →]
```

- Impact score shown as colored badge: 9–10 red, 7–8 orange, 5–6 yellow, 1–4 gray
- Direction icon: 🟢 bullish, 🔴 bearish, ⚪ neutral
- AI-tagged articles show 🤖 badge
- Max 20 articles shown (user can expand to see more)

#### Section 2: 🤖 AI & NVDA Watch

- Subheader: "🤖 AI & NVDA Watch"
- Caption: "Stories impacting the AI trade: NVDA, AMD, AVGO, MSFT, GOOGL, META"
- Sentiment summary line at top: *"5 bullish · 2 bearish · 1 neutral AI stories today"*
- Same card format as Section 1
- Filtered to articles where `ai_trade_tag=True`
- Empty state: "No AI-specific stories in the last hour. Check back soon."

#### Section 3: 📊 Your Stocks

- Subheader: "📊 Your Stocks"
- Caption: "News grouped by company — S&P 100 + CIFR"
- CIFR pinned at top always
- Each company shown as a collapsible `st.expander`
- Inside: up to 3 article cards per company
- Companies with no news in the last hour hidden by default
- Empty state per company: shown only if expanded

---

## Data Flow

```
load_news_digest(cache_buster)          # @st.cache_data ttl=3600
  ├── fetch_market_news()               # NewsAPI: global/macro terms
  ├── fetch_ai_news()                   # NewsAPI: AI/chip terms
  ├── fetch_company_news(sp100 + CIFR)  # NewsAPI: per company
  └── summarize_articles(all_articles)  # Anthropic API: batch
        └── returns list[ArticleSummary]

render_news_digest(summaries)           # app/ui/news_digest.py
  ├── render_market_feed(summaries)
  ├── render_ai_watch(summaries)
  └── render_stock_news(summaries, sp100_tickers)
```

---

## New Files

| File | Purpose |
|------|---------|
| `app/data/news_digest_fetcher.py` | NewsAPI queries for macro, AI, and company news |
| `app/data/ai_summarizer.py` | Anthropic API summarization + JSON parsing |
| `app/ui/news_digest.py` | Full tab UI: market feed, AI watch, stock news |

## Modified Files

| File | Change |
|------|--------|
| `main.py` | Add `load_news_digest()` cached function; add "📰 News Digest" tab |
| `app/data/sp100_tickers.py` | New file: hardcoded S&P 100 ticker + company name list + CIFR |

---

## S&P 100 Ticker Universe

Hardcoded list of S&P 100 tickers with company names (for display and querying). CIFR added manually. Does not scrape Wikipedia (avoids the fragility seen with NASDAQ-100).

---

## Error Handling

- If NewsAPI fails: show "Unable to load news. Check your NewsAPI key." with retry button
- If Anthropic API fails: show raw headline + snippet without AI summary; do not crash
- If Anthropic API key missing: show informational message "Add ANTHROPIC_API_KEY to your secrets to enable AI summaries"
- Rate limit handling: if NewsAPI returns 429, show cached results with a timestamp

---

## Secrets Required

Add to `.streamlit/secrets.toml`:
```toml
ANTHROPIC_API_KEY = "sk-ant-..."
```

User must create account at console.anthropic.com and generate an API key.

---

## Requirements File

Add to `requirements.txt`:
```
anthropic>=0.25.0
```
