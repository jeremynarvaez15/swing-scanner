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


def render_sidebar(fear_greed_data: dict, reddit_data: dict):
    with st.sidebar:
        st.title("📊 Market Mood")
        st.caption("How is the overall market feeling right now?")

        # --- Fear & Greed ---
        score = fear_greed_data.get("score", 50)
        label = fear_greed_data.get("label", "Neutral")
        color = _FG_COLORS.get(label, "#FFCC00")
        meaning = _FG_MEANING.get(label, "")

        st.markdown("### CNN Fear & Greed Index")
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

        # --- Reddit Trending ---
        st.markdown("### 🔥 Reddit Trending (24h)")
        st.caption("Stocks being talked about most by everyday investors on Reddit.")

        # Handle both old format (int) and new format (dict)
        has_sentiment = any(isinstance(v, dict) for v in reddit_data.values()) if reddit_data else False

        if reddit_data and has_sentiment:
            sorted_mentions = sorted(
                [(t, d) for t, d in reddit_data.items() if isinstance(d, dict) and d.get("count", 0) > 0],
                key=lambda x: x[1]["count"],
                reverse=True,
            )[:10]

            if sorted_mentions:
                for ticker, data in sorted_mentions:
                    count = data["count"]
                    sentiment = data.get("sentiment", "neutral")
                    sent_color = _SENTIMENT_COLOR[sentiment]
                    sent_icon = _SENTIMENT_ICON[sentiment]
                    bar_width = min(100, int(count / max(sorted_mentions[0][1]["count"], 1) * 100))

                    st.markdown(
                        f'<div style="margin:6px 0;padding:6px 8px;background:#1E2130;border-radius:8px;'
                        f'border-left:3px solid {sent_color}">'
                        f'<div style="display:flex;justify-content:space-between;align-items:center">'
                        f'<span style="font-weight:bold;color:#fff">${ticker}</span>'
                        f'<span style="font-size:11px;color:{sent_color}">{sent_icon} {sentiment.capitalize()}</span>'
                        f'</div>'
                        f'<div style="font-size:11px;color:#aaa">{count} mention{"s" if count != 1 else ""}</div>'
                        f'<div style="background:#333;border-radius:3px;height:4px;margin-top:4px">'
                        f'<div style="background:{sent_color};border-radius:3px;height:4px;width:{bar_width}%"></div>'
                        f'</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
            else:
                st.caption("No trending stocks found in the last 24 hours.")

        elif reddit_data and not has_sentiment:
            # Fallback for old int format
            sorted_mentions = sorted(
                [(t, c) for t, c in reddit_data.items() if isinstance(c, int) and c > 0],
                key=lambda x: x[1], reverse=True
            )[:10]
            for ticker, count in sorted_mentions:
                st.markdown(f"**${ticker}** — {count} mentions")
        else:
            st.caption("No Reddit data available. Add Reddit API credentials in Settings to enable this.")

        with st.expander("❓ What is Reddit Trending?"):
            st.markdown("""
Reddit is a popular website where millions of people discuss stocks in communities like **WallStreetBets**, **r/investing**, and **r/stocks**.

This section shows which stocks are being talked about the most in the last 24 hours — and whether the conversation is **positive** (people are excited/bullish) or **negative** (people are worried/bearish).

**Why does it matter?**
When a stock suddenly gets a lot of attention on Reddit, it can signal that something is happening — breaking news, a big price move, or growing excitement. Combined with the Signal Score, it helps confirm whether a trade idea has momentum behind it.

🟢 **Positive** — People are excited, bullish, expecting it to go up

🔴 **Negative** — People are worried, bearish, expecting it to go down

⚪ **Neutral** — Mixed or factual discussion, no clear direction
            """)
