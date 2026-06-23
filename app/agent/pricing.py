"""Rough cost estimation for observability only (never billing).

Prices are approximate USD per 1M tokens and will drift; keep them updated or
override per deployment. Unknown models yield ``None`` (cost not estimated).
"""

# (input_price_per_1M, output_price_per_1M)
_PRICES_PER_MILLION: dict[str, tuple[float, float]] = {
    "gpt-4.1": (2.0, 8.0),
    "gpt-4.1-mini": (0.4, 1.6),
    "gpt-4o": (2.5, 10.0),
    "gpt-4o-mini": (0.15, 0.6),
}


def estimate_cost_usd(model: str, input_tokens: int, output_tokens: int) -> float | None:
    prices = _PRICES_PER_MILLION.get(model)
    if prices is None:
        return None
    input_price, output_price = prices
    return round((input_tokens * input_price + output_tokens * output_price) / 1_000_000, 6)
