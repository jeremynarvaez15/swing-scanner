import praw
from datetime import datetime, timezone
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

_analyzer = SentimentIntensityAnalyzer()


def fetch_reddit_mentions(
    tickers: list[str],
    client_id: str,
    client_secret: str,
    user_agent: str,
) -> dict[str, dict]:
    """
    Count ticker mentions in WSB + investing subreddits over last 24h.
    Returns dict: ticker -> {"count": int, "sentiment": "positive"|"negative"|"neutral", "score": float}
    """
    results = {t: {"count": 0, "sentiment": "neutral", "score": 0.0, "snippets": []} for t in tickers}
    if not client_id or not client_secret:
        return results

    try:
        reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent,
        )
        ticker_set = set(t.upper() for t in tickers)
        cutoff = datetime.now(timezone.utc).timestamp() - 86400

        for sub_name in ["wallstreetbets", "investing", "stocks"]:
            try:
                sub = reddit.subreddit(sub_name)
                for post in sub.new(limit=200):
                    if post.created_utc < cutoff:
                        break
                    text = f"{post.title} {post.selftext}"
                    text_upper = text.upper()
                    for ticker in ticker_set:
                        if f" {ticker} " in f" {text_upper} " or f"${ticker}" in text_upper:
                            results[ticker]["count"] += 1
                            results[ticker]["snippets"].append(post.title)
            except Exception:
                continue

        # Score sentiment for each ticker based on collected post titles
        for ticker in tickers:
            snippets = results[ticker]["snippets"]
            if snippets:
                scores = [_analyzer.polarity_scores(s)["compound"] for s in snippets]
                avg = sum(scores) / len(scores)
                results[ticker]["score"] = round(avg, 3)
                if avg >= 0.05:
                    results[ticker]["sentiment"] = "positive"
                elif avg <= -0.05:
                    results[ticker]["sentiment"] = "negative"
                else:
                    results[ticker]["sentiment"] = "neutral"

    except Exception:
        pass

    return results
