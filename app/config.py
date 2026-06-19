import streamlit as st

_DEFAULTS = {
    "watchlist": ["AAPL", "TSLA", "NVDA", "MSFT", "AMZN"],
    "buy_threshold": 70,
    "sell_threshold": 30,
    "cooldown_hours": 4,
    "alert_volume_surge": True,
    "alert_news_surge": True,
    "watchlist_only_alerts": False,
    "to_phone_number": "",
}


def load_config() -> dict:
    if "config" not in st.session_state:
        st.session_state["config"] = _DEFAULTS.copy()
    return st.session_state["config"]


def save_config(config: dict):
    st.session_state["config"] = config


def get_twilio_cfg() -> dict:
    try:
        return {
            "account_sid": st.secrets["TWILIO_ACCOUNT_SID"],
            "auth_token": st.secrets["TWILIO_AUTH_TOKEN"],
            "from_number": st.secrets["TWILIO_FROM_NUMBER"],
            "to_number": st.session_state.get("config", {}).get("to_phone_number", ""),
        }
    except Exception:
        return {}
