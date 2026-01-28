"""Binary sensor entities for SVOTC."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, SENSOR_OBJECT_IDS
from .coordinator import SVOTCCoordinator


@dataclass(frozen=True, kw_only=True)
class SVOTCBinarySensorDescription(BinarySensorEntityDescription):
    """Describe a SVOTC binary sensor."""

    key: str


BINARY_SENSOR_DESCRIPTIONS: tuple[SVOTCBinarySensorDescription, ...] = (
    SVOTCBinarySensorDescription(
        key="tomorrow_available",
        translation_key="tomorrow_available",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up SVOTC binary sensors."""
    coordinator: SVOTCCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        SVOTCBinarySensorEntity(coordinator, entry, description)
        for description in BINARY_SENSOR_DESCRIPTIONS
    )


class SVOTCBinarySensorEntity(CoordinatorEntity, BinarySensorEntity):
    """Representation of a SVOTC binary sensor."""

    _attr_should_poll = False

    def __init__(
        self,
        coordinator: SVOTCCoordinator,
        entry: ConfigEntry,
        description: SVOTCBinarySensorDescription,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self.entity_description = description

        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_suggested_object_id = SENSOR_OBJECT_IDS.get(
            description.key, f"{DOMAIN}_{description.key}"
        )
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="SVOTC",
        )

    @property
    def is_on(self) -> bool | None:
        """Return True if the binary sensor is on."""
        value = self.coordinator.data.get(self.entity_description.key)
        if value is None:
            return None
        return bool(value)

    @property
    def available(self) -> bool:
        """Return entity availability."""
        return self.coordinator.last_update_success
