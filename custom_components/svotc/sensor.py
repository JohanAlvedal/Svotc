"""Sensor entities for SVOTC."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.const import UnitOfTemperature

from .const import DOMAIN
from .coordinator import SVOTCCoordinator


@dataclass(frozen=True, kw_only=True)
class SVOTCSensorDescription(SensorEntityDescription):
    """Describe a SVOTC sensor."""

    key: str


SENSOR_DESCRIPTIONS: tuple[SVOTCSensorDescription, ...] = (
    SVOTCSensorDescription(
        key="virtual_outdoor_temperature",
        translation_key="svotc",
    ),
)


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


class SVOTCSensorEntity(SensorEntity):
    """Representation of a SVOTC sensor."""

    def __init__(
        self,
        coordinator: SVOTCCoordinator,
        entry: ConfigEntry,
        description: SVOTCSensorDescription,
    ) -> None:
        """Initialize the sensor."""
        self.coordinator = coordinator
        self.entity_description = description
        self._attr_unique_id = f"{DOMAIN}_sensor"
        self._attr_suggested_object_id = "svotc"
        self._attr_device_class = SensorDeviceClass.TEMPERATURE
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="SVOTC",
        )

    @property
    def native_value(self) -> object:
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
            "dynamic_target_c": data.get("dynamic_target_temperature"),
            "mode": self.coordinator.values.get("mode"),
            "indoor_temp_c": data.get("indoor_temperature"),
            "outdoor_temp_c": data.get("outdoor_temperature"),
        }

    @property
    def available(self) -> bool:
        """Return entity availability."""
        return self.coordinator.last_update_success
