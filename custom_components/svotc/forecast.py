"""Forecast helpers for SVOTC."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util


def _parse_datetime(value: Any) -> datetime | None:
    """Parse forecast datetime values."""
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        return dt_util.parse_datetime(value)
    return None


async def _get_hourly_forecast_list(
    hass: HomeAssistant,
    entity_id: str,
) -> list[dict[str, Any]] | None:
    """Fetch hourly forecast list using weather.get_forecasts service."""
    try:
        resp = await hass.services.async_call(
            "weather",
            "get_forecasts",
            {"type": "hourly"},
            target={"entity_id": entity_id},
            blocking=True,
            return_response=True,  # returns dict mapping entity_id -> {"forecast": [...]}
        )
    except TypeError:
        # Fallback for older HA versions without return_response support.
        return None
    except Exception:
        return None

    if not isinstance(resp, dict):
        return None

    entity_payload = resp.get(entity_id)
    if not isinstance(entity_payload, dict):
        # Some setups may return a single payload under another key; try first dict value.
        entity_payload = next((v for v in resp.values() if isinstance(v, dict)), None)

    if not isinstance(entity_payload, dict):
        return None

    forecast = entity_payload.get("forecast")
    if not isinstance(forecast, list):
        return None

    # Ensure entries are dicts
    return [e for e in forecast if isinstance(e, dict)]


def min_outdoor_next_6h_from_forecast(forecast: list[dict[str, Any]], now: datetime) -> float | None:
    """Return the minimum forecast temperature for the next 6 hours from a forecast list."""
    now = dt_util.as_local(now) if now.tzinfo else dt_util.as_local(dt_util.now())
    window_end = now + timedelta(hours=6)

    temps: list[float] = []
    for entry in forecast:
        entry_time = _parse_datetime(entry.get("datetime"))
        if entry_time is not None:
            entry_time = dt_util.as_local(entry_time) if entry_time.tzinfo else entry_time
            if entry_time < now or entry_time > window_end:
                continue
        try:
            temps.append(float(entry.get("temperature")))
        except (TypeError, ValueError):
            continue

    # Fallback: take first 6 entries if datetimes are missing/unreliable
    if not temps:
        for entry in forecast[:6]:
            try:
                temps.append(float(entry.get("temperature")))
            except (TypeError, ValueError):
                continue

    return min(temps) if temps else None


async def min_outdoor_next_6h(hass: HomeAssistant, entity_id: str, now: datetime) -> float | None:
    """Return the minimum hourly forecast temperature for the next 6 hours for a weather entity."""
    forecast = await _get_hourly_forecast_list(hass, entity_id)
    if not forecast:
        return None
    return min_outdoor_next_6h_from_forecast(forecast, now)
