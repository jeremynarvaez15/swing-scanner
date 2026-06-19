import streamlit as st
from app.config import load_config, save_config


def render_settings():
    config = load_config()

    with st.expander("⚙️ Settings", expanded=False):
        st.subheader("My Watchlist")
        watchlist_raw = st.text_input(
            "Tickers (comma-separated, max 5)",
            value=", ".join(config["watchlist"]),
            help="Example: AAPL, TSLA, NVDA, MSFT, AMZN",
        )
        watchlist = [t.strip().upper() for t in watchlist_raw.split(",") if t.strip()][:5]

        st.subheader("Alert Thresholds")
        buy_threshold = st.slider("Buy signal threshold (score ≥)", 50, 95, config["buy_threshold"], step=5)
        sell_threshold = st.slider("Sell signal threshold (score ≤)", 5, 50, config["sell_threshold"], step=5)
        cooldown_hours = st.slider("Alert cooldown (hours)", 1, 48, config["cooldown_hours"])

        st.subheader("Alert Types")
        alert_volume = st.toggle("Alert on volume surge", value=config["alert_volume_surge"])
        alert_news = st.toggle("Alert on news surge", value=config["alert_news_surge"])
        watchlist_only = st.toggle("Watchlist alerts only", value=config["watchlist_only_alerts"])

        st.subheader("SMS Alerts")
        to_phone = st.text_input(
            "Your phone number (E.164 format, e.g. +12125551234)",
            value=config["to_phone_number"],
        )

        if st.button("💾 Save Settings"):
            save_config({
                "watchlist": watchlist,
                "buy_threshold": buy_threshold,
                "sell_threshold": sell_threshold,
                "cooldown_hours": cooldown_hours,
                "alert_volume_surge": alert_volume,
                "alert_news_surge": alert_news,
                "watchlist_only_alerts": watchlist_only,
                "to_phone_number": to_phone,
            })
            st.success("Settings saved!")
