"""Data coordinator for SVOTC."""

from __future__ import annotations

from datetime import datetime, timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from .const import (
    CONF_INDOOR_TEMPERATURE,
    CONF_OUTDOOR_TEMPERATURE,
    DEFAULT_BRAKE_AGGRESSIVENESS,
    DEFAULT_COMFORT_TEMPERATURE,
    DEFAULT_HEAT_AGGRESSIVENESS,
    DEFAULT_MODE,
    DEFAULT_VACATION_TEMPERATURE,
    DOMAIN,
    CONF_PRICE_ENTITY,
    CONF_WEATHER_ENTITY,
)
from .decision import DecisionInput, decide
from .forecast import min_outdoor_next_6h
from .mapping import max_abs_offset
from .prices import classify_price, extract_price_series
from .ramp import max_delta_per_update, ramp_offset

_LOGGER = logging.getLogger(__name__)

_GRACE_PERIOD = timedelta(seconds=60)
_GLITCH_HOLD = timedelta(seconds=60)


class SVOTCCoordinator(DataUpdateCoordinator[dict[str, object]]):
    """Coordinate SVOTC state updates."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=60),
        )
        self.entry = entry
        self.values: dict[str, object] = {
            "brake_aggressiveness": DEFAULT_BRAKE_AGGRESSIVENESS,
            "heat_aggressiveness": DEFAULT_HEAT_AGGRESSIVENESS,
            "comfort_temperature": DEFAULT_COMFORT_TEMPERATURE,
            "vacation_temperature": DEFAULT_VACATION_TEMPERATURE,
            "mode": DEFAULT_MODE,
        }
        self._start_time = dt_util.utcnow()
        self._last_complete_time: datetime | None = None
        self._last_output: dict[str, object] | None = None
        self._last_offset: float = 0.0
        self._last_price_state: str | None = None
        self._last_price_state_changed: datetime | None = None

    def _read_temperature(self, entity_id: str | None) -> float | None:
        """Read a temperature from a Home Assistant state."""
        if not entity_id:
            return None
        state = self.hass.states.get(entity_id)
        if state is None or state.state in ("unknown", "unavailable"):
            return None
        try:
            return float(state.state)
        except ValueError:
            return None

    def _read_state(self, entity_id: str | None) -> object | None:
        """Read a raw state for an entity."""
        if not entity_id:
            return None
        state = self.hass.states.get(entity_id)
        if state is None or state.state in ("unknown", "unavailable"):
            return None
        return state

    def _missing_reason(
        self,
        indoor: float | None,
        outdoor: float | None,
        price_available: bool,
        forecast_available: bool,
    ) -> str:
        """Return a reason code for missing critical inputs."""
        if indoor is None or outdoor is None:
            return "MISSING_INDOOR"
        if not price_available and not forecast_available:
            return "MISSING_BOTH"
        if not price_available:
            return "MISSING_PRICE"
        if not forecast_available:
            return "MISSING_FORECAST"
        return "MISSING_BOTH"

    async def async_set_value(self, key: str, value: object) -> None:
        """Persist a value and refresh coordinator data."""
        self.values[key] = value
        await self.async_request_refresh()

    async def _async_update_data(self) -> dict[str, object]:
        """Fetch data for SVOTC sensors."""
        now = dt_util.utcnow()
        entry_data = {**self.entry.data, **self.entry.options}
        indoor_temp = self._read_temperature(entry_data.get(CONF_INDOOR_TEMPERATURE))
        outdoor_temp = self._read_temperature(entry_data.get(CONF_OUTDOOR_TEMPERATURE))
        price_state = self._read_state(entry_data.get(CONF_PRICE_ENTITY))
        weather_state = self._read_state(entry_data.get(CONF_WEATHER_ENTITY))

        mode = self.values.get("mode", DEFAULT_MODE)

        if mode == "Vacation":
            dynamic_target = self.values.get(
                "vacation_temperature", DEFAULT_VACATION_TEMPERATURE
            )
        else:
            dynamic_target = self.values.get(
                "comfort_temperature", DEFAULT_COMFORT_TEMPERATURE
            )

        current_price, price_series = extract_price_series(price_state, now)
        price_available = current_price is not None and len(price_series) > 0
        price_class = classify_price(current_price, price_series)
        forecast_min = min_outdoor_next_6h(weather_state, now)
        forecast_available = forecast_min is not None

        critical_missing = False
        if entry_data.get(CONF_INDOOR_TEMPERATURE) and indoor_temp is None:
            critical_missing = True
        if entry_data.get(CONF_OUTDOOR_TEMPERATURE) and outdoor_temp is None:
            critical_missing = True
        if entry_data.get(CONF_PRICE_ENTITY) and not price_available:
            critical_missing = True
        if entry_data.get(CONF_WEATHER_ENTITY) and not forecast_available:
            critical_missing = True

        if not critical_missing:
            self._last_complete_time = now

        in_grace = now - self._start_time <= _GRACE_PERIOD
        missing_duration = (
            now - self._last_complete_time
            if self._last_complete_time is not None
            else None
        )

        if critical_missing and not in_grace and self._last_output is not None:
            if missing_duration is not None and missing_duration <= _GLITCH_HOLD:
                held = dict(self._last_output)
                held["status"] = "Holding (sensor glitch)"
                held["reason_code"] = "TEMP_GLITCH_HOLD"
                return held

        if critical_missing and not in_grace:
            reason_code = self._missing_reason(
                indoor_temp, outdoor_temp, price_available, forecast_available
            )
            status = reason_code.replace("_", " ").title()
            if outdoor_temp is not None:
                offset = 0.0
                virtual_outdoor = outdoor_temp
            elif self._last_output is not None:
                offset = float(self._last_output.get("offset", 0.0))
                virtual_outdoor = self._last_output.get(
                    "virtual_outdoor_temperature"
                )
            else:
                offset = 0.0
                virtual_outdoor = None
            result = {
                "indoor_temperature": indoor_temp,
                "outdoor_temperature": outdoor_temp,
                "virtual_outdoor_temperature": virtual_outdoor,
                "offset": offset,
                "dynamic_target_temperature": dynamic_target,
                "status": status,
                "reason_code": reason_code,
            }
            self._last_output = result
            self._last_offset = offset
            return result

        if in_grace and critical_missing:
            offset = 0.0
            virtual_outdoor = (
                outdoor_temp + offset if outdoor_temp is not None else None
            )
            result = {
                "indoor_temperature": indoor_temp,
                "outdoor_temperature": outdoor_temp,
                "virtual_outdoor_temperature": virtual_outdoor,
                "offset": offset,
                "dynamic_target_temperature": dynamic_target,
                "status": "Startup grace",
                "reason_code": "NEUTRAL",
            }
            self._last_output = result
            self._last_offset = offset
            return result

        decision = decide(
            DecisionInput(
                mode=str(mode),
                indoor_temp=indoor_temp,
                outdoor_temp=outdoor_temp,
                dynamic_target=float(dynamic_target),
                brake_aggressiveness=int(
                    self.values.get("brake_aggressiveness", DEFAULT_BRAKE_AGGRESSIVENESS)
                ),
                heat_aggressiveness=int(
                    self.values.get("heat_aggressiveness", DEFAULT_HEAT_AGGRESSIVENESS)
                ),
                price_class=price_class,
                forecast_min_next_6h=forecast_min,
                price_available=price_available,
                forecast_available=forecast_available,
                now=now,
                last_price_state=self._last_price_state,
                last_price_state_changed=self._last_price_state_changed,
            )
        )

        max_delta = max_delta_per_update(max_abs_offset())
        offset = ramp_offset(self._last_offset, decision.target_offset, max_delta)
        virtual_outdoor = (
            outdoor_temp + offset if outdoor_temp is not None else None
        )
        if virtual_outdoor is not None:
            clamped_virtual = max(-25.0, min(25.0, virtual_outdoor))
            if clamped_virtual != virtual_outdoor:
                offset = clamped_virtual - outdoor_temp
                virtual_outdoor = clamped_virtual

        if decision.price_state is not None:
            if decision.price_state != self._last_price_state:
                self._last_price_state = decision.price_state
                self._last_price_state_changed = now

        result = {
            "indoor_temperature": indoor_temp,
            "outdoor_temperature": outdoor_temp,
            "virtual_outdoor_temperature": virtual_outdoor,
            "offset": offset,
            "dynamic_target_temperature": dynamic_target,
            "status": decision.status,
            "reason_code": decision.reason_code,
        }
        self._last_output = result
        self._last_offset = offset
        return {
            **result,
        }
