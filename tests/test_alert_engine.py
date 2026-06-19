from unittest.mock import patch
from app.alerts.alert_engine import check_and_alert, _format_sms, _is_in_cooldown

def _thresholds():
    return {"buy": 70, "sell": 30, "cooldown_hours": 4}

def _twilio():
    return {"account_sid": "AC123", "auth_token": "tok", "from_number": "+10000000000", "to_number": "+19999999999"}

def test_no_alert_when_score_neutral():
    assert check_and_alert("AAPL", 55, 150.0, {}, {}, _thresholds(), {}, _twilio()) is False

def test_alert_sent_when_score_above_buy_threshold():
    with patch("app.alerts.alert_engine.send_sms", return_value=True) as mock_sms:
        sent = check_and_alert("AAPL", 75, 150.0,
            {"rsi": 28, "macd_signal": "bullish", "volume_surge": True},
            {"sentiment_label": "positive", "surge": False},
            _thresholds(), {}, _twilio())
    assert sent is True
    mock_sms.assert_called_once()

def test_no_alert_during_cooldown():
    import time
    cooldowns = {"AAPL": time.time()}
    with patch("app.alerts.alert_engine.send_sms", return_value=True):
        assert check_and_alert("AAPL", 75, 150.0, {}, {}, _thresholds(), cooldowns, _twilio()) is False

def test_sms_format_contains_required_fields():
    msg = _format_sms("NVDA", "BUY", 78, 124.50, {"rsi": 28, "macd_signal": "bullish", "volume_surge": True}, {"sentiment_label": "positive", "surge": False})
    assert "NVDA" in msg
    assert "BUY" in msg
    assert "78" in msg
    assert "124.50" in msg
