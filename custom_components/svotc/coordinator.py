"""Data coordinator for SVOTC."""

from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    CONF_INDOOR_TEMPERATURE,
    CONF_OUTDOOR_TEMPERATURE,
    DEFAULT_BRAKE_AGGRESSIVENESS,
    DEFAULT_COMFORT_TEMPERATURE,
    DEFAULT_HEAT_AGGRESSIVENESS,
    DEFAULT_MODE,
    DEFAULT_VACATION_TEMPERATURE,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


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

    async def async_set_value(self, key: str, value: object) -> None:
        """Persist a value and refresh coordinator data."""
        self.values[key] = value
        await self.async_request_refresh()

    async def _async_update_data(self) -> dict[str, object]:
        """Fetch data for SVOTC sensors."""
        entry_data = {**self.entry.data, **self.entry.options}
        indoor_temp = self._read_temperature(entry_data.get(CONF_INDOOR_TEMPERATURE))
        outdoor_temp = self._read_temperature(entry_data.get(CONF_OUTDOOR_TEMPERATURE))

        offset = 0.0
        virtual_outdoor = (
            outdoor_temp + offset if outdoor_temp is not None else None
        )
        mode = self.values.get("mode", DEFAULT_MODE)

        if mode == "Vacation":
            dynamic_target = self.values.get(
                "vacation_temperature", DEFAULT_VACATION_TEMPERATURE
            )
        else:
            dynamic_target = self.values.get(
                "comfort_temperature", DEFAULT_COMFORT_TEMPERATURE
            )

        return {
            "indoor_temperature": indoor_temp,
            "outdoor_temperature": outdoor_temp,
            "virtual_outdoor_temperature": virtual_outdoor,
            "offset": offset,
            "dynamic_target_temperature": dynamic_target,
            "status": "stub",
            "reason_code": "not_implemented",
        }
