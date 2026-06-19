import time
from app.alerts.twilio_sms import send_sms

_APP_URL = "swingscanner.streamlit.app"


def _format_sms(ticker: str, signal: str, score: int, price: float, indicators: dict, sentiment: dict) -> str:
    reasons = []
    rsi = indicators.get("rsi", 50)
    if rsi <= 30:
        reasons.append("RSI oversold")
    elif rsi >= 70:
        reasons.append("RSI overbought")
    if indicators.get("macd_signal") == "bullish":
        reasons.append("MACD bullish cross")
    elif indicators.get("macd_signal") == "bearish":
        reasons.append("MACD bearish cross")
    if indicators.get("volume_surge"):
        reasons.append("volume surge")
    if sentiment.get("sentiment_label") == "positive":
        reasons.append("positive news")
    elif sentiment.get("sentiment_label") == "negative":
        reasons.append("negative news")
    if sentiment.get("surge"):
        reasons.append("news surge")

    reason_str = " + ".join(reasons) if reasons else "multiple signals aligned"

    return (
        f"SWING SCANNER ALERT\n"
        f"Ticker: {ticker}\n"
        f"Signal: {signal} (Score: {score})\n"
        f"Price: ${price:.2f}\n"
        f"Reason: {reason_str}\n"
        f"View: {_APP_URL}"
    )


def _is_in_cooldown(ticker: str, cooldowns: dict, cooldown_hours: float) -> bool:
    if ticker not in cooldowns:
        return False
    elapsed = time.time() - cooldowns[ticker]
    return elapsed < cooldown_hours * 3600


def check_and_alert(
    ticker: str,
    score: int,
    price: float,
    indicators: dict,
    sentiment: dict,
    thresholds: dict,
    cooldowns: dict,
    twilio_cfg: dict,
) -> bool:
    """Check thresholds and send SMS if triggered. Returns True if alert sent."""
    buy_threshold = thresholds.get("buy", 70)
    sell_threshold = thresholds.get("sell", 30)
    cooldown_hours = thresholds.get("cooldown_hours", 4)

    if score > buy_threshold:
        signal = "BUY"
    elif score < sell_threshold:
        signal = "SELL"
    else:
        return False

    if _is_in_cooldown(ticker, cooldowns, cooldown_hours):
        return False

    body = _format_sms(ticker, signal, score, price, indicators, sentiment)
    sent = send_sms(
        to_number=twilio_cfg["to_number"],
        body=body,
        account_sid=twilio_cfg["account_sid"],
        auth_token=twilio_cfg["auth_token"],
        from_number=twilio_cfg["from_number"],
    )
    if sent:
        cooldowns[ticker] = time.time()
    return sent
