import requests


def fetch_fear_greed() -> dict:
    """Fetch CNN Fear & Greed Index from their public JSON endpoint."""
    url = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        current = data["fear_and_greed"]
        score = int(round(current["score"]))
        label = current.get("rating", _score_to_label(score)).replace("_", " ").title()
        return {
            "score": score,
            "label": label,
            "timestamp": current.get("timestamp", ""),
        }
    except Exception:
        return {"score": 50, "label": "Neutral", "timestamp": ""}


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
