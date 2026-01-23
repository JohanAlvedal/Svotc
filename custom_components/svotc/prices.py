"""Helpers for price classification."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from homeassistant.core import State
from homeassistant.util import dt as dt_util


def _parse_datetime(value: Any) -> datetime | None:
    """Parse a datetime value if possible."""
    if isinstance(value, datetime):
        return dt_util.as_utc(value)
    if isinstance(value, str):
        parsed = dt_util.parse_datetime(value)
        if parsed is None:
            return None
        return dt_util.as_utc(parsed)
    return None


def extract_price_entries(state: State | None) -> list[dict[str, object]]:
    """Extract price entries from a state attribute payload."""
    if state is None or state.state in ("unknown", "unavailable"):
        return []
    data = state.attributes.get("data")
    if not isinstance(data, list):
        return []
    entries: list[dict[str, object]] = []
    for entry in data:
        if not isinstance(entry, dict):
            continue
        start = _parse_datetime(entry.get("start"))
        end = _parse_datetime(entry.get("end"))
        if start is None or end is None:
            continue
        try:
            price = float(entry["price"])
        except (KeyError, TypeError, ValueError):
            continue
        entries.append({"start": start, "end": end, "price": price})
    return entries


def select_current_price(
    entries: list[dict[str, object]], now: datetime
) -> float | None:
    """Select the current price from matching entries."""
    for entry in sorted(entries, key=lambda item: item["start"]):
        start = entry["start"]
        end = entry["end"]
        if isinstance(start, datetime) and isinstance(end, datetime):
            if start <= now < end:
                return float(entry["price"])
    return None


def _percentile(values: list[float], percentile: float) -> float:
    """Compute a percentile value for a list."""
    if not values:
        raise ValueError("Values required for percentile calculation")
    ordered = sorted(values)
    position = (len(ordered) - 1) * percentile
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    if upper == lower:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def price_percentiles(prices: list[float]) -> tuple[float | None, float | None]:
    """Return (p30, p70) percentiles for prices."""
    if not prices:
        return None, None
    try:
        return _percentile(prices, 0.30), _percentile(prices, 0.70)
    except ValueError:
        return None, None


def classify_price(current_price: float | None, prices: list[float]) -> str | None:
    """Classify the current price as cheap, neutral, or expensive."""
    if current_price is None or not prices:
        return None
    p30, p70 = price_percentiles(prices)
    if p30 is None or p70 is None:
        return None
    if current_price <= p30:
        return "cheap"
    if current_price >= p70:
        return "expensive"
    return "neutral"
