import streamlit as st

_FG_COLORS = {
    "Extreme Fear": "#FF4444",
    "Fear": "#FF8800",
    "Neutral": "#FFCC00",
    "Greed": "#88CC00",
    "Extreme Greed": "#00CC44",
}


def render_sidebar(fear_greed_data: dict, reddit_mentions: dict):
    with st.sidebar:
        st.title("📊 Market Mood")

        score = fear_greed_data.get("score", 50)
        label = fear_greed_data.get("label", "Neutral")
        color = _FG_COLORS.get(label, "#FFCC00")

        st.markdown("### CNN Fear & Greed Index")
        st.markdown(
            f'<div style="font-size:48px;font-weight:bold;color:{color};text-align:center">{score}</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div style="text-align:center;color:{color};font-size:18px">{label}</div>',
            unsafe_allow_html=True,
        )
        st.progress(score / 100)

        st.divider()

        st.markdown("### 🔥 Reddit Trending (24h)")
        if reddit_mentions:
            sorted_mentions = sorted(reddit_mentions.items(), key=lambda x: x[1], reverse=True)[:10]
            for ticker, count in sorted_mentions:
                if count > 0:
                    st.markdown(f"**${ticker}** — {count} mentions")
        else:
            st.caption("No Reddit data available")
