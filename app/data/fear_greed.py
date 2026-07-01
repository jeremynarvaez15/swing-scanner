import requests


def fetch_fear_greed() -> dict:
    """Fetch Fear & Greed Index from Alternative.me (free, unbiased)."""
    try:
        url = "https://api.alternative.me/fng/?limit=1&format=json"
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers, timeout=8)
        resp.raise_for_status()
        data = resp.json()
        entry = data["data"][0]
        score = int(entry["value"])
        label = entry.get("value_classification", _score_to_label(score)).title()
        return {"score": score, "label": label, "timestamp": entry.get("timestamp", ""), "source": "Alternative.me"}
    except Exception:
        return {"score": 50, "label": "Neutral", "timestamp": "", "source": "unavailable"}


def _score_to_label(score: int) -> str:
    if score <= 25:
        return "Extreme Fear"
    if score <= 45:
        return "Fear"
    if score <= 55:
        return "Neutral"
    if score <= 75:
        return "Greed"
    return "Extreme Greed"
