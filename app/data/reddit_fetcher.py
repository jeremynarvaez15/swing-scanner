import praw
from datetime import datetime, timezone


def fetch_reddit_mentions(
    tickers: list[str],
    client_id: str,
    client_secret: str,
    user_agent: str,
) -> dict[str, int]:
    """
    Count ticker mentions in WSB + investing subreddits over last 24h.
    Returns dict: ticker -> mention count.
    """
    counts = {t: 0 for t in tickers}
    if not client_id or not client_secret:
        return counts

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
                    text = f"{post.title} {post.selftext}".upper()
                    for ticker in ticker_set:
                        if f" {ticker} " in f" {text} " or f"${ticker}" in text:
                            counts[ticker] += 1
            except Exception:
                continue
    except Exception:
        pass

    return counts
