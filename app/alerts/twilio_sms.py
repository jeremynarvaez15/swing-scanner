from twilio.rest import Client


def send_sms(to_number: str, body: str, account_sid: str, auth_token: str, from_number: str) -> bool:
    """Send SMS via Twilio. Returns True on success, False on failure."""
    try:
        client = Client(account_sid, auth_token)
        client.messages.create(body=body, from_=from_number, to=to_number)
        return True
    except Exception:
        return False
