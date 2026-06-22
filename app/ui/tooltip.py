def ticker_tooltip(ticker: str, ma_20=None, ma_50=None, ma_200=None, price=None) -> str:
    """
    Return an HTML span for a ticker that shows MA20/50/200 on hover.
    Uses the browser's native title tooltip — works on any device.
    """
    lines = []
    if price:
        lines.append(f"Price:   ${price:.2f}")
    if ma_20:
        arrow = "↑" if price and price > ma_20 else "↓"
        lines.append(f"MA20:  ${ma_20:.2f}  {arrow}")
    if ma_50:
        arrow = "↑" if price and price > ma_50 else "↓"
        lines.append(f"MA50:  ${ma_50:.2f}  {arrow}")
    if ma_200:
        arrow = "↑" if price and price > ma_200 else "↓"
        lines.append(f"MA200: ${ma_200:.2f}  {arrow}")

    tooltip_text = "\n".join(lines) if lines else "No MA data"

    return (
        f'<span title="{tooltip_text}" style="cursor:help;border-bottom:1px dotted #aaa">'
        f'${ticker}'
        f'</span>'
    )
