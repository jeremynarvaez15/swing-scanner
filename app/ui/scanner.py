import streamlit as st
import pandas as pd
from app.ui.tooltip import ticker_tooltip


def render_scanner(scan_results: list[dict]):
    st.subheader("🔍 Market Scanner")

    if not scan_results:
        st.info("Scanner data loading...")
        return

    df = pd.DataFrame(scan_results)

    col1, col2, col3 = st.columns(3)
    with col1:
        min_score = st.slider("Min Signal Score", 0, 100, 0)
    with col2:
        sectors = ["All"] + sorted(df["sector"].dropna().unique().tolist())
        selected_sector = st.selectbox("Sector", sectors)
    with col3:
        signal_filter = st.selectbox("Signal Type", ["All", "BUY (≥70)", "SELL (≤30)", "Neutral"])

    filtered = df[df["score"] >= min_score].copy()
    if selected_sector != "All":
        filtered = filtered[filtered["sector"] == selected_sector]
    if signal_filter == "BUY (≥70)":
        filtered = filtered[filtered["score"] >= 70]
    elif signal_filter == "SELL (≤30)":
        filtered = filtered[filtered["score"] <= 30]
    elif signal_filter == "Neutral":
        filtered = filtered[(filtered["score"] > 30) & (filtered["score"] < 70)]

    filtered = filtered.sort_values("score", ascending=False)
    st.caption(f"Showing {len(filtered)} of {len(df)} stocks")

    filtered["Ticker"] = filtered["ticker"].apply(lambda t: f"${t}")

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

    available = [c for c in display_cols if c in filtered.columns]
    display_df = filtered[available].copy()
    display_df = display_df.rename(columns={k: v for k, v in display_cols.items() if k in available})

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

    if "Price" in display_df.columns:
        display_df["Price"] = display_df["Price"].apply(lambda x: f"${x:.2f}")
    if "Day %" in display_df.columns:
        display_df["Day %"] = display_df["Day %"].apply(lambda x: f"{x:+.2f}%")
    if "RSI" in display_df.columns:
        display_df["RSI"] = display_df["RSI"].apply(lambda x: f"{x:.1f}")
    for ma_col in ["MA20", "MA50", "MA200"]:
        if ma_col in display_df.columns:
            display_df[ma_col] = display_df[ma_col].apply(
                lambda x: f"${x:.2f}" if pd.notna(x) and x == x else "N/A"
            )
    if "Vol Ratio" in display_df.columns:
        display_df["Vol Ratio"] = display_df["Vol Ratio"].apply(lambda x: f"{x:.1f}x")
    if "52W Position" in display_df.columns:
        display_df["52W Position"] = display_df["52W Position"].apply(
            lambda x: f"{x:.0f}%" if pd.notna(x) else "N/A"
        )
    if "Daily Move ($)" in display_df.columns:
        display_df["Daily Move ($)"] = display_df["Daily Move ($)"].apply(
            lambda x: f"${x:.2f}" if pd.notna(x) else "N/A"
        )
    if "Earnings" in display_df.columns:
        display_df["Earnings"] = display_df["Earnings"].apply(
            lambda x: f"⚠️ {int(x)}d" if pd.notna(x) and x <= 14 else (f"{int(x)}d" if pd.notna(x) else "—")
        )

    col_config = {}
    if "Setup Score" in display_df.columns:
        col_config["Setup Score"] = st.column_config.ProgressColumn("Setup Score", min_value=0, max_value=100, format="%d")

    st.caption("💡 Tip: Sort any column by clicking its header. Filter by sector or signal type above.")
    st.dataframe(display_df, use_container_width=True, hide_index=True, column_config=col_config)
