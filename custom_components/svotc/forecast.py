"""Forecast helpers for SVOTC."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from homeassistant.core import State
from homeassistant.util import dt as dt_util


def _parse_datetime(value: Any) -> datetime | None:
    """Parse forecast datetime values."""
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        return dt_util.parse_datetime(value)
    return None


def min_outdoor_next_6h(state: State | None, now: datetime) -> float | None:
    """Return the minimum forecast temperature for the next 6 hours."""
    if state is None:
        return None
    forecast = state.attributes.get("forecast")
    if not isinstance(forecast, list):
        return None

    window_end = now + timedelta(hours=6)
    temps: list[float] = []
    for entry in forecast:
        if not isinstance(entry, dict):
            continue
        entry_time = _parse_datetime(entry.get("datetime"))
        if entry_time is not None:
            if entry_time < now or entry_time > window_end:
                continue
        try:
            temps.append(float(entry.get("temperature")))
        except (TypeError, ValueError):
            continue

    if not temps:
        for entry in forecast[:6]:
            if not isinstance(entry, dict):
                continue
            try:
                temps.append(float(entry.get("temperature")))
            except (TypeError, ValueError):
                continue

    if not temps:
        return None
    return min(temps)
