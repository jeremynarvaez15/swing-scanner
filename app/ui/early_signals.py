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
