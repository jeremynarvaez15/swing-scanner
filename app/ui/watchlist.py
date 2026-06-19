import streamlit as st
import plotly.graph_objects as go


def _score_color(score: int) -> str:
    if score >= 70:
        return "#00C853"
    if score <= 30:
        return "#FF1744"
    return "#9E9E9E"


def _mini_chart(history_df):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=history_df.index[-30:],
        y=history_df["Close"].iloc[-30:],
        mode="lines",
        line=dict(color="#00C853", width=2),
        showlegend=False,
    ))
    fig.update_layout(
        height=120,
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
    )
    return fig


def render_watchlist(stocks: list[dict]):
    st.subheader("⭐ My Watchlist")
    if not stocks:
        st.info("Add tickers in Settings to populate your watchlist.")
        return

    cols = st.columns(len(stocks))
    for col, stock in zip(cols, stocks):
        with col:
            ticker = stock["ticker"]
            price = stock.get("price", 0)
            change_pct = stock.get("change_pct", 0)
            score = stock.get("score", 50)
            indicators = stock.get("indicators", {})
            sentiment = stock.get("sentiment", {})
            history_df = stock.get("history_df")

            color = _score_color(score)
            change_icon = "▲" if change_pct >= 0 else "▼"
            change_color = "#00C853" if change_pct >= 0 else "#FF1744"

            st.markdown(f"#### ${ticker}")
            st.markdown(
                f'<span style="font-size:22px;font-weight:bold">${price:.2f}</span> '
                f'<span style="color:{change_color}">{change_icon} {abs(change_pct):.2f}%</span>',
                unsafe_allow_html=True,
            )
            st.markdown(
                f'<div style="background:{color};border-radius:8px;padding:4px 8px;'
                f'display:inline-block;font-weight:bold;color:#000;margin:4px 0">Score: {score}</div>',
                unsafe_allow_html=True,
            )

            if history_df is not None and len(history_df) >= 30:
                st.plotly_chart(_mini_chart(history_df), use_container_width=True)

            rsi = indicators.get("rsi", 50)
            rsi_color = "#FF1744" if rsi >= 70 else ("#00C853" if rsi <= 30 else "#9E9E9E")
            st.markdown(
                f'<span style="background:{rsi_color};border-radius:4px;padding:2px 6px;'
                f'font-size:12px;color:#fff">RSI {rsi:.0f}</span>',
                unsafe_allow_html=True,
            )

            sent_label = sentiment.get("sentiment_label", "neutral")
            st.caption(f"Sentiment: {sent_label.capitalize()}")

            for h in sentiment.get("scored_headlines", [])[:3]:
                icon = "🟢" if h.get("label") == "positive" else ("🔴" if h.get("label") == "negative" else "⚪")
                title = h.get("title", "")
                st.caption(f"{icon} {title[:75]}{'...' if len(title) > 75 else ''}")
