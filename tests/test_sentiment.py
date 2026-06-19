from app.signals.sentiment import score_sentiment

def test_positive_headlines_return_positive_score():
    headlines = [
        {"title": "Company reports record profits and raises guidance", "source": "CNBC", "published_at": "2026-06-18T10:00:00Z"},
        {"title": "Strong earnings beat expectations, stock rallies", "source": "Reuters", "published_at": "2026-06-18T09:00:00Z"},
    ]
    result = score_sentiment(headlines)
    assert result["sentiment_score"] > 0.0
    assert result["sentiment_label"] == "positive"

def test_negative_headlines_return_negative_score():
    headlines = [
        {"title": "Company faces bankruptcy risk amid falling revenue", "source": "CNBC", "published_at": "2026-06-18T10:00:00Z"},
        {"title": "Crash warning: analysts downgrade stock to sell", "source": "Reuters", "published_at": "2026-06-18T09:00:00Z"},
    ]
    result = score_sentiment(headlines)
    assert result["sentiment_score"] < 0.0
    assert result["sentiment_label"] == "negative"

def test_empty_headlines_returns_neutral():
    result = score_sentiment([])
    assert result["sentiment_score"] == 0.0
    assert result["sentiment_label"] == "neutral"
    assert result["surge"] is False

def test_scored_headlines_have_label():
    headlines = [{"title": "Stock rises on good news", "source": "MarketWatch", "published_at": "2026-06-18T10:00:00Z"}]
    result = score_sentiment(headlines)
    assert len(result["scored_headlines"]) == 1
    assert result["scored_headlines"][0]["label"] in ("positive", "negative", "neutral")

def test_surge_detected_when_many_headlines():
    headlines = [{"title": f"Headline {i}", "source": "CNBC", "published_at": "2026-06-18T10:00:00Z"} for i in range(10)]
    result = score_sentiment(headlines, daily_average=3.0)
    assert result["surge"] is True
