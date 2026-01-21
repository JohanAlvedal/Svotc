"""Helpers for price classification."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from typing import Any

from homeassistant.core import State
from homeassistant.util import dt as dt_util


def _parse_datetime(value: Any) -> datetime | None:
    """Parse a datetime value if possible."""
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        return dt_util.parse_datetime(value)
    return None


def _extract_price_values(entries: Iterable[Any], now: datetime) -> list[float]:
    """Extract price values from iterable entries."""
    values: list[float] = []
    for entry in entries:
        if isinstance(entry, dict):
            if "start" in entry or "startsAt" in entry or "datetime" in entry:
                start = (
                    entry.get("start")
                    or entry.get("startsAt")
                    or entry.get("datetime")
                )
                parsed = _parse_datetime(start)
                if parsed is not None and parsed < now:
                    continue
            for key in ("value", "price", "total", "energy"):
                if key in entry:
                    try:
                        values.append(float(entry[key]))
                    except (TypeError, ValueError):
                        pass
                    break
        else:
            try:
                values.append(float(entry))
            except (TypeError, ValueError):
                continue
    return values


def extract_price_series(
    state: State | None, now: datetime
) -> tuple[float | None, list[float]]:
    """Extract current price and a price series from an entity."""
    if state is None or state.state in ("unknown", "unavailable"):
        return None, []
    try:
        current_price = float(state.state)
    except ValueError:
        current_price = None

    attributes = state.attributes
    series: list[float] = []
    for key in ("raw_today", "raw_tomorrow", "today", "tomorrow", "prices"):
        data = attributes.get(key)
        if isinstance(data, list):
            series.extend(_extract_price_values(data, now))

    if not series and current_price is not None:
        series = [current_price]

    return current_price, series


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


def classify_price(current_price: float | None, prices: list[float]) -> str | None:
    """Classify the current price as cheap, neutral, or expensive."""
    if current_price is None or not prices:
        return None
    try:
        p30 = _percentile(prices, 0.30)
        p70 = _percentile(prices, 0.70)
    except ValueError:
        return None
    if current_price <= p30:
        return "cheap"
    if current_price >= p70:
        return "expensive"
    return "neutral"
