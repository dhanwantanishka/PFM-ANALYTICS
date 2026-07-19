"""Display formatting helpers."""

from __future__ import annotations


def format_currency(value: float, symbol: str = "₹") -> str:
    """Format a numeric amount as currency."""
    return f"{symbol}{value:,.0f}"


def format_pct(value: float, decimals: int = 1) -> str:
    """Format a percentage value."""
    return f"{value:.{decimals}f}%"


def trend_delta(current: float, previous: float) -> str | None:
    """Return a human-readable delta string for metric cards."""
    if previous == 0:
        return None
    change = ((current - previous) / abs(previous)) * 100
    sign = "+" if change >= 0 else ""
    return f"{sign}{change:.1f}%"
