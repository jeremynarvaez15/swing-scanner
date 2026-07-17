import json

_PROMPT = """\
You are a financial analyst. Summarize this news article for a retail swing trader.

Headline: {title}
Content: {content}

Return ONLY valid JSON with these exact keys:
- summary: 2-3 sentences explaining what happened and why it matters to stock investors
- impact_score: integer 1-10 (10 = major market-moving event)
- impact_direction: one of "bullish", "bearish", "neutral" for US equities overall
- ai_trade_tag: true if this story is about AI, semiconductors, data centers, or AI model development; false otherwise
"""

_FALLBACK = {
    "summary": "",
    "impact_score": 5,
    "impact_direction": "neutral",
    "ai_trade_tag": False,
}


def _summarize_one(client, article: dict) -> dict:
    content = (article.get("description") or "")[:500]
    prompt = _PROMPT.format(title=article["title"], content=content)
    try:
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=256,
            messages=[{"role": "user", "content": prompt}],
        )
        text = message.content[0].text.strip()
        parsed = json.loads(text)
        return {
            "summary": str(parsed.get("summary", "")),
            "impact_score": int(parsed.get("impact_score", 5)),
            "impact_direction": str(parsed.get("impact_direction", "neutral")),
            "ai_trade_tag": bool(parsed.get("ai_trade_tag", False)),
        }
    except Exception:
        return dict(_FALLBACK)


def summarize_articles(articles: list[dict], api_key: str) -> list[dict]:
    """Enrich each article dict with AI summary fields. Safe to call with empty api_key."""
    if not api_key or not articles:
        return [{**a, **_FALLBACK} for a in articles]

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
    except Exception:
        return [{**a, **_FALLBACK} for a in articles]

    result = []
    for article in articles:
        enriched = dict(article)
        enriched.update(_summarize_one(client, article))
        result.append(enriched)
    return result
