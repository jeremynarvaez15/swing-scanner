from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

_analyzer = SentimentIntensityAnalyzer()


def _label(compound: float) -> str:
    if compound >= 0.05:
        return "positive"
    if compound <= -0.05:
        return "negative"
    return "neutral"


def score_sentiment(headlines: list[dict], daily_average: float = 3.0) -> dict:
    """
    Score a list of headline dicts using VADER sentiment analysis.
    daily_average: expected number of headlines per day for surge detection.
    """
    if not headlines:
        return {
            "sentiment_score": 0.0,
            "sentiment_label": "neutral",
            "surge": False,
            "scored_headlines": [],
        }

    scored = []
    compounds = []
    for h in headlines:
        vs = _analyzer.polarity_scores(h.get("title", ""))
        compound = vs["compound"]
        compounds.append(compound)
        scored.append({**h, "label": _label(compound)})

    avg_compound = sum(compounds) / len(compounds)
    surge = len(headlines) >= daily_average * 2

    return {
        "sentiment_score": round(avg_compound, 4),
        "sentiment_label": _label(avg_compound),
        "surge": surge,
        "scored_headlines": scored,
    }
