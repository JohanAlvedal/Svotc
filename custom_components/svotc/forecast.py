"""Forecast helpers for SVOTC."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from homeassistant.core import HomeAssistant, State
from homeassistant.util import dt as dt_util


def _parse_datetime(value: Any) -> datetime | None:
    """Parse forecast datetime values."""
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        return dt_util.parse_datetime(value)
    return None


async def get_forecast_list(
    hass: HomeAssistant,
    entity_id: str,
    forecast_type: str = "hourly",
) -> list[dict[str, Any]] | None:
    """Fetch forecast list for a weather entity via weather.get_forecasts.

    Returns a list of forecast dict entries, or None if not available.
    """
    try:
        resp = await hass.services.async_call(
            "weather",
            "get_forecasts",
            {"type": forecast_type},
            target={"entity_id": entity_id},
            blocking=True,
            return_response=True,
        )
    except Exception:
        return None

    if not isinstance(resp, dict):
        return None

    payload = resp.get(entity_id)
    if not isinstance(payload, dict):
        # Some setups may return a single payload under another key; try first dict value.
        payload = next((v for v in resp.values() if isinstance(v, dict)), None)

    if not isinstance(payload, dict):
        return None

    forecast = payload.get("forecast")
    if not isinstance(forecast, list):
        return None

    return [e for e in forecast if isinstance(e, dict)]


def min_temp_next_hours_from_forecast(
    forecast: list[dict[str, Any]],
    now: datetime,
    hours: int = 12,
) -> float | None:
    """Return the minimum forecast temperature for the next N hours from a forecast list."""
    window_end = now + timedelta(hours=hours)

    temps: list[float] = []
    for entry in forecast:
        entry_time = _parse_datetime(entry.get("datetime"))
        if entry_time is not None:
            if entry_time < now or entry_time > window_end:
                continue
        try:
            temps.append(float(entry.get("temperature")))
        except (TypeError, ValueError):
            continue

    # Fallback: take first N entries if datetimes are missing/unreliable
    if not temps:
        for entry in forecast[:hours]:
            try:
                temps.append(float(entry.get("temperature")))
            except (TypeError, ValueError):
                continue

    return min(temps) if temps else None


async def min_outdoor_next_12h(
    hass: HomeAssistant,
    weather_entity_id: str,
    now: datetime,
) -> float | None:
    """Return the minimum outdoor temperature for the next 12 hours.

    Uses the service-based forecast API if available, with a fallback to legacy
    state.attributes["forecast"] if present.
    """
    now = dt_util.as_local(now)

    # Preferred: service-based forecast retrieval
    forecast = await get_forecast_list(hass, weather_entity_id, forecast_type="hourly")
    if forecast:
        return min_temp_next_hours_from_forecast(forecast, now, hours=12)

    # Fallback: legacy forecast stored as state attribute (some providers/older HA)
    state: State | None = hass.states.get(weather_entity_id)
    if state is None:
        return None

    attr_forecast = state.attributes.get("forecast")
    if isinstance(attr_forecast, list):
        cleaned = [e for e in attr_forecast if isinstance(e, dict)]
        if cleaned:
            return min_temp_next_hours_from_forecast(cleaned, now, hours=12)

    return None
