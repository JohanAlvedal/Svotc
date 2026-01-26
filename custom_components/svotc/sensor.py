"""Sensor entities for SVOTC."""

from __future__ import annotations

from dataclasses import dataclass
import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import SVOTCCoordinator

_LOGGER = logging.getLogger(__name__)

@dataclass(frozen=True, kw_only=True)
class SVOTCSensorDescription(SensorEntityDescription):
    """Describe a SVOTC sensor."""

    key: str


SENSOR_DESCRIPTIONS: tuple[SVOTCSensorDescription, ...] = (
    SVOTCSensorDescription(
        key="virtual_outdoor_temperature",
        translation_key="virtual_outdoor_temperature",
    ),
)

# Keep entity_id readable and stable: sensor.svotc_<key>
SENSOR_OBJECT_IDS: dict[str, str] = {
    "virtual_outdoor_temperature": f"{DOMAIN}_virtual_outdoor_temperature",
}

# Legacy unique_ids used before switching to per-entry unique IDs.
# Used by entity_id migration to find and migrate older entities.
SENSOR_UNIQUE_ID_KEYS: dict[str, str] = {
    "virtual_outdoor_temperature": f"{DOMAIN}_sensor",
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up SVOTC sensors."""
    coordinator: SVOTCCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        SVOTCSensorEntity(coordinator, entry, description)
        for description in SENSOR_DESCRIPTIONS
    )


class SVOTCSensorEntity(CoordinatorEntity, SensorEntity, RestoreEntity):
    """Representation of a SVOTC sensor."""

    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_should_poll = False

    def __init__(
        self,
        coordinator: SVOTCCoordinator,
        entry: ConfigEntry,
        description: SVOTCSensorDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description

        # Unique per config entry + key (supports multiple entries safely)
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"

        # Desired entity_id: sensor.svotc_<key> (no entry_id in the object_id)
        self._attr_suggested_object_id = SENSOR_OBJECT_IDS.get(
            description.key, f"{DOMAIN}_{description.key}"
        )

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="SVOTC",
        )

    async def async_added_to_hass(self) -> None:
        """Restore ramp baseline on startup."""
        await super().async_added_to_hass()
        last_state = await self.async_get_last_state()
        if last_state is None:
            return

        restored_value: float = 0.0
        attrs = last_state.attributes or {}
        raw_value = attrs.get("applied_offset_c")
        if raw_value is None:
            raw_value = attrs.get("offset_c")
        if raw_value is None:
            raw_value = attrs.get("last_applied_offset_c")
        try:
            restored_value = float(raw_value)
        except (TypeError, ValueError):
            restored_value = 0.0

        self.coordinator._last_offset = restored_value
        self.coordinator._last_offset_source = "restored_state"
        _LOGGER.debug(
            "Restored last_applied_offset_c=%.3f from previous state (source=hass_state).",
            restored_value,
        )
        await self.coordinator.async_request_refresh()

    @property
    def native_value(self) -> float | None:
        """Return the sensor value."""
        value = self.coordinator.data.get(self.entity_description.key)
        if value is None:
            return None
        return float(value)

    @property
    def extra_state_attributes(self) -> dict[str, object]:
        """Return additional sensor attributes."""
        data = self.coordinator.data
        return {
            "status": data.get("status"),
            "reason_code": data.get("reason_code"),
            "offset_c": data.get("offset"),
            "requested_offset_c": data.get("requested_offset"),
            "applied_offset_c": data.get("applied_offset"),
            "ramp_limited": data.get("ramp_limited"),
            "max_delta_per_step": data.get("max_delta_per_step"),
            "last_applied_offset_c": data.get("last_applied_offset"),
            "dynamic_target_c": data.get("dynamic_target_temperature"),
            "mode": self.coordinator.values.get("mode"),
            "indoor_temp_c": data.get("indoor_temperature"),
            "outdoor_temp_c": data.get("outdoor_temperature"),
            "price_entities_used": data.get("price_entities_used"),
            "prices_count_today": data.get("prices_count_today"),
            "prices_count_tomorrow": data.get("prices_count_tomorrow"),
            "tomorrow_available": data.get("tomorrow_available"),
            "prices_count_total": data.get("prices_count_total"),
            "current_price": data.get("current_price"),
            "price_state": data.get("price_state"),
            "p30": data.get("p30"),
            "p70": data.get("p70"),
            "missing_inputs": data.get("missing_inputs"),
        }

    @property
    def available(self) -> bool:
        """Return entity availability."""
        return self.coordinator.last_update_success
