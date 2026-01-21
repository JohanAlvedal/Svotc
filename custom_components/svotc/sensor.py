"""Sensor entities for SVOTC."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import SVOTCCoordinator


@dataclass(frozen=True, kw_only=True)
class SVOTCSensorDescription(SensorEntityDescription):
    """Describe a SVOTC sensor."""

    key: str


SENSOR_DESCRIPTIONS: tuple[SVOTCSensorDescription, ...] = (
    SVOTCSensorDescription(
        key="virtual_outdoor_temperature",
        translation_key="virtual_outdoor_temperature",
    ),
    SVOTCSensorDescription(
        key="offset",
        translation_key="offset",
    ),
    SVOTCSensorDescription(
        key="dynamic_target_temperature",
        translation_key="dynamic_target_temperature",
    ),
    SVOTCSensorDescription(
        key="status",
        translation_key="status",
    ),
    SVOTCSensorDescription(
        key="reason_code",
        translation_key="reason_code",
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
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="SVOTC",
        )

    @property
    def native_value(self) -> object:
        """Return the sensor value."""
        return self.coordinator.data.get(self.entity_description.key)

    @property
    def available(self) -> bool:
        """Return entity availability."""
        return self.coordinator.last_update_success
