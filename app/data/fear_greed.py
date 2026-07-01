import requests


def fetch_fear_greed() -> dict:
    """
    Fetch Fear & Greed Index. Tries CNN first, falls back to alternative.me.
    """
    result = _try_cnn()
    if result:
        return result
    result = _try_alternative_me()
    if result:
        return result
    return {"score": 50, "label": "Neutral", "timestamp": "", "source": "fallback"}


def _try_cnn() -> dict:
    urls = [
        "https://production.dataviz.cnn.io/index/fearandgreed/graphdata",
        "https://fear-and-greed-index.p.rapidapi.com/v1/fgi",
    ]
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
    }
    for url in urls:
        try:
            resp = requests.get(url, headers=headers, timeout=8)
            if resp.status_code == 200:
                data = resp.json()
                if "fear_and_greed" in data:
                    current = data["fear_and_greed"]
                    score = int(round(float(current["score"])))
                    label = current.get("rating", _score_to_label(score))
                    label = label.replace("_", " ").title()
                    return {"score": score, "label": label, "timestamp": current.get("timestamp", ""), "source": "CNN"}
        except Exception:
            continue
    return {}


def _try_alternative_me() -> dict:
    """Alternative.me provides a stock market Fear & Greed index via free API."""
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
        return {}


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
