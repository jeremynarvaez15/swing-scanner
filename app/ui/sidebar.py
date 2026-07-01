import streamlit as st

_FG_COLORS = {
    "Extreme Fear": "#FF4444",
    "Fear": "#FF8800",
    "Neutral": "#FFCC00",
    "Greed": "#88CC00",
    "Extreme Greed": "#00CC44",
}

_FG_MEANING = {
    "Extreme Fear": "Investors are panicking. Historically a good time to look for buys.",
    "Fear": "Market is cautious. Tread carefully but watch for opportunities.",
    "Neutral": "Balanced market. Follow individual stock signals.",
    "Greed": "Investors are confident. Good for momentum trades.",
    "Extreme Greed": "Market may be overheated. Consider taking profits.",
}

_SENTIMENT_COLOR = {
    "positive": "#00C853",
    "negative": "#FF1744",
    "neutral": "#9E9E9E",
}

_SENTIMENT_ICON = {
    "positive": "🟢",
    "negative": "🔴",
    "neutral": "⚪",
}


def render_sidebar(fear_greed_data: dict, stocktwits_data: list):
    with st.sidebar:
        st.title("📊 Market Mood")
        st.caption("How is the overall market feeling right now?")

        # --- Fear & Greed ---
        score = fear_greed_data.get("score", 50)
        label = fear_greed_data.get("label", "Neutral")
        color = _FG_COLORS.get(label, "#FFCC00")
        meaning = _FG_MEANING.get(label, "")

        st.markdown("### Fear & Greed Index")
        st.markdown(
            f'<div style="font-size:52px;font-weight:bold;color:{color};text-align:center">{score}</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div style="text-align:center;color:{color};font-size:20px;font-weight:bold">{label}</div>',
            unsafe_allow_html=True,
        )
        st.progress(score / 100)
        st.markdown(
            f'<div style="font-size:12px;color:#aaa;text-align:center;margin-top:4px;font-style:italic">'
            f'{meaning}</div>',
            unsafe_allow_html=True,
        )
        source = fear_greed_data.get("source", "")
        if source:
            st.caption(f"Source: {source}")

        with st.expander("❓ What does this mean?"):
            st.markdown("""
**0–25 😱 Extreme Fear** — Investors are panicking and selling. Stocks are often cheaper than they should be. Many experienced traders see this as a buying opportunity.

**26–45 😟 Fear** — The market is nervous. Be selective and cautious.

**46–55 😐 Neutral** — No strong emotion. Judge each stock on its own merits.

**56–75 😊 Greed** — Investors are buying confidently. Good for momentum.

**76–100 🤑 Extreme Greed** — Everyone is piling in. The market may be overheated — consider taking profits on winning positions.

*Famous investor Warren Buffett's rule: "Be fearful when others are greedy, and greedy when others are fearful."*
            """)

        st.divider()

        # --- StockTwits Trending ---
        st.markdown("### 🔥 StockTwits Trending")
        st.caption("Stocks traders are buzzing about right now.")

        if stocktwits_data:
            max_watchers = max((s.get("watchers", 1) for s in stocktwits_data), default=1)
            for stock in stocktwits_data[:10]:
                ticker = stock["ticker"]
                sentiment = stock.get("sentiment", "neutral")
                bullish_pct = stock.get("bullish_pct", 50)
                watchers = stock.get("watchers", 0)
                sent_color = _SENTIMENT_COLOR[sentiment]
                sent_icon = _SENTIMENT_ICON[sentiment]
                bar_width = min(100, int(watchers / max_watchers * 100))

                st.markdown(
                    f'<div style="margin:6px 0;padding:6px 8px;background:#1E2130;border-radius:8px;'
                    f'border-left:3px solid {sent_color}">'
                    f'<div style="display:flex;justify-content:space-between;align-items:center">'
                    f'<span style="font-weight:bold;color:#fff">${ticker}</span>'
                    f'<span style="font-size:11px;color:{sent_color}">{sent_icon} {bullish_pct}% bullish</span>'
                    f'</div>'
                    f'<div style="font-size:11px;color:#aaa">{watchers:,} watchers</div>'
                    f'<div style="background:#333;border-radius:3px;height:4px;margin-top:4px">'
                    f'<div style="background:{sent_color};border-radius:3px;height:4px;width:{bar_width}%"></div>'
                    f'</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
        else:
            st.caption("Unable to load StockTwits data. Please try refreshing.")

        with st.expander("❓ What is StockTwits Trending?"):
            st.markdown("""
**StockTwits** is a social network specifically for traders and investors — like Twitter but only for stocks. Millions of traders post their opinions, trades, and analysis there every day.

This section shows the **most-watched stocks** on StockTwits right now, along with how traders are feeling about them.

**Why does it matter?**
When a stock is trending on StockTwits, it means active traders are paying attention to it. Combined with the Signal Score, it helps confirm whether a trade idea has real momentum behind it.

🟢 **Bullish (60%+)** — Most traders expect the stock to go up

🔴 **Bearish (40% or less bullish)** — Most traders expect the stock to go down

⚪ **Neutral (40–60%)** — Traders are split, no clear direction

The **% bullish** number shows exactly how many traders are feeling positive vs. negative.
            """)
