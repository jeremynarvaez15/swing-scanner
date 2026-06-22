import streamlit as st
import plotly.graph_objects as go
from app.ui.tooltip import ticker_tooltip


def _score_color(score: int) -> str:
    if score >= 70:
        return "#00C853"
    if score <= 30:
        return "#FF1744"
    return "#9E9E9E"


def _verdict(score: int, days_to_earnings, sentiment_label: str) -> tuple[str, str, str]:
    """Return (emoji, label, color) trade verdict."""
    earnings_risk = days_to_earnings is not None and days_to_earnings <= 14
    if score >= 70 and not earnings_risk and sentiment_label != "negative":
        return "✅", "Looks Interesting", "#00C853"
    if score <= 30 and not earnings_risk and sentiment_label != "positive":
        return "❌", "Not Right Now", "#FF1744"
    return "⚠️", "Use Caution", "#FF8800"


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


def _week52_bar(pct: float) -> str:
    """Render a simple HTML progress bar showing 52-week position."""
    filled = int(pct)
    color = "#00C853" if pct <= 30 else ("#FF1744" if pct >= 70 else "#FF8800")
    return (
        f'<div style="margin:4px 0">'
        f'<div style="font-size:11px;color:#aaa;margin-bottom:2px">'
        f'52-Week Range &nbsp; <span style="color:#aaa">Low</span> '
        f'<span style="float:right;color:#aaa">High</span></div>'
        f'<div style="background:#333;border-radius:4px;height:8px;width:100%">'
        f'<div style="background:{color};border-radius:4px;height:8px;width:{filled}%"></div>'
        f'</div>'
        f'<div style="font-size:11px;color:{color};text-align:center;margin-top:2px">'
        f'{pct:.0f}% of yearly range</div>'
        f'</div>'
    )


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
            details = stock.get("details", {})

            color = _score_color(score)
            change_icon = "▲" if change_pct >= 0 else "▼"
            change_color = "#00C853" if change_pct >= 0 else "#FF1744"
            sent_label = sentiment.get("sentiment_label", "neutral")
            days_to_earnings = details.get("days_to_earnings")

            # --- Header ---
            ma_20 = indicators.get("ma_20")
            ma_50 = indicators.get("ma_50")
            ma_200 = indicators.get("ma_200")
            st.markdown(f"#### ${ticker}")
            st.markdown(
                f'<span style="font-size:22px;font-weight:bold">${price:.2f}</span> '
                f'<span style="color:{change_color}">{change_icon} {abs(change_pct):.2f}%</span>',
                unsafe_allow_html=True,
            )

            # --- Signal Score ---
            st.markdown(
                f'<div style="background:{color};border-radius:8px;padding:4px 8px;'
                f'display:inline-block;font-weight:bold;color:#000;margin:4px 0">Score: {score}</div>',
                unsafe_allow_html=True,
            )

            # --- Verdict Box ---
            verdict_emoji, verdict_label, verdict_color = _verdict(score, days_to_earnings, sent_label)
            st.markdown(
                f'<div style="background:{verdict_color}22;border:1px solid {verdict_color};'
                f'border-radius:8px;padding:6px 10px;margin:6px 0;text-align:center">'
                f'<span style="font-size:18px">{verdict_emoji}</span> '
                f'<span style="color:{verdict_color};font-weight:bold">{verdict_label}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

            # --- Earnings Warning ---
            if days_to_earnings is not None:
                if days_to_earnings <= 7:
                    st.markdown(
                        f'<div style="background:#FF1744;border-radius:6px;padding:4px 8px;'
                        f'color:#fff;font-size:12px;text-align:center">⚠️ Earnings in {days_to_earnings} days — HIGH RISK</div>',
                        unsafe_allow_html=True,
                    )
                elif days_to_earnings <= 14:
                    st.markdown(
                        f'<div style="background:#FF8800;border-radius:6px;padding:4px 8px;'
                        f'color:#fff;font-size:12px;text-align:center">⚠️ Earnings in {days_to_earnings} days — Use caution</div>',
                        unsafe_allow_html=True,
                    )

            # --- Mini Chart ---
            if history_df is not None and len(history_df) >= 30:
                st.plotly_chart(_mini_chart(history_df), use_container_width=True)

            # --- 52-Week Bar ---
            week52_pct = details.get("week52_pct")
            if week52_pct is not None:
                st.markdown(_week52_bar(week52_pct), unsafe_allow_html=True)

            # --- Key Stats ---
            atr = details.get("atr")
            target_up = details.get("target_up")
            target_down = details.get("target_down")

            if atr:
                st.markdown(
                    f'<div style="font-size:12px;color:#aaa;margin:4px 0">'
                    f'📏 Typical daily move: <b style="color:#fff">${atr:.2f}</b> '
                    f'<span style="color:#666">— helps set stop-loss</span></div>',
                    unsafe_allow_html=True,
                )
            if target_up and target_down:
                st.markdown(
                    f'<div style="font-size:12px;margin:4px 0">'
                    f'🎯 <span style="color:#00C853">Upside target: ${target_up:.2f}</span> &nbsp;|&nbsp; '
                    f'<span style="color:#FF1744">Downside risk: ${target_down:.2f}</span></div>',
                    unsafe_allow_html=True,
                )

            # --- Moving Averages ---
            if ma_20 or ma_50 or ma_200:
                def _ma_color(ma_val):
                    if not ma_val or not price:
                        return "#9E9E9E"
                    return "#00C853" if price > ma_val else "#FF1744"

                st.markdown(
                    f'<div style="background:#1E2130;border-radius:8px;padding:8px;margin:6px 0">'
                    f'<div style="font-size:11px;color:#aaa;margin-bottom:4px">📉 Moving Averages '
                    f'<span style="color:#555">(hover = price above/below MA)</span></div>'
                    f'<div style="display:flex;justify-content:space-between">'
                    + (f'<div style="text-align:center">'
                       f'<div style="font-size:10px;color:#aaa">20-Day</div>'
                       f'<div style="font-size:13px;font-weight:bold;color:{_ma_color(ma_20)}">${ma_20:.2f}</div>'
                       f'<div style="font-size:10px;color:{_ma_color(ma_20)}">{"▲ Above" if price and price > ma_20 else "▼ Below"}</div>'
                       f'</div>' if ma_20 else '')
                    + (f'<div style="text-align:center">'
                       f'<div style="font-size:10px;color:#aaa">50-Day</div>'
                       f'<div style="font-size:13px;font-weight:bold;color:{_ma_color(ma_50)}">${ma_50:.2f}</div>'
                       f'<div style="font-size:10px;color:{_ma_color(ma_50)}">{"▲ Above" if price and price > ma_50 else "▼ Below"}</div>'
                       f'</div>' if ma_50 else '')
                    + (f'<div style="text-align:center">'
                       f'<div style="font-size:10px;color:#aaa">200-Day</div>'
                       f'<div style="font-size:13px;font-weight:bold;color:{_ma_color(ma_200)}">${ma_200:.2f}</div>'
                       f'<div style="font-size:10px;color:{_ma_color(ma_200)}">{"▲ Above" if price and price > ma_200 else "▼ Below"}</div>'
                       f'</div>' if ma_200 else '')
                    + f'</div></div>',
                    unsafe_allow_html=True,
                )

            # --- Indicators ---
            rsi = indicators.get("rsi", 50)
            rsi_color = "#FF1744" if rsi >= 70 else ("#00C853" if rsi <= 30 else "#9E9E9E")
            rsi_tip = "Oversold — may bounce up 🟢" if rsi <= 30 else ("Overbought — may pull back 🔴" if rsi >= 70 else "Neutral ⚪")
            macd = indicators.get("macd_signal", "neutral")
            macd_tip = {"bullish": "Momentum building up 🟢", "bearish": "Momentum fading 🔴", "neutral": "No clear momentum ⚪"}.get(macd, "")

            st.markdown(
                f'<div style="margin:6px 0">'
                f'<span title="RSI measures if stock is overbought or oversold" '
                f'style="background:{rsi_color};border-radius:4px;padding:2px 6px;font-size:11px;color:#fff;margin-right:4px">'
                f'RSI {rsi:.0f}</span>'
                f'<span style="font-size:11px;color:#aaa">{rsi_tip}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                f'<div style="font-size:11px;color:#aaa;margin:2px 0">'
                f'📊 MACD: {macd_tip}</div>',
                unsafe_allow_html=True,
            )

            # --- Sentiment ---
            sent_color = "#00C853" if sent_label == "positive" else ("#FF1744" if sent_label == "negative" else "#9E9E9E")
            st.markdown(
                f'<div style="font-size:12px;margin:4px 0">'
                f'📰 News sentiment: <span style="color:{sent_color};font-weight:bold">{sent_label.capitalize()}</span></div>',
                unsafe_allow_html=True,
            )

            for h in sentiment.get("scored_headlines", [])[:2]:
                icon = "🟢" if h.get("label") == "positive" else ("🔴" if h.get("label") == "negative" else "⚪")
                title = h.get("title", "")
                st.caption(f"{icon} {title[:70]}{'...' if len(title) > 70 else ''}")
