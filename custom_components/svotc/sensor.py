"""Sensor entities for SVOTC."""

from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Callable

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, SENSOR_OBJECT_IDS
from .coordinator import SVOTCCoordinator

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class SVOTCSensorDescription(SensorEntityDescription):
    """Describe a SVOTC sensor."""

    key: str


@dataclass(frozen=True, kw_only=True)
class SVOTCDataSensorDescription(SensorEntityDescription):
    """Describe a SVOTC data sensor."""

    key: str
    value_fn: Callable[[object], float | str | None]


def _as_float(value: object) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _as_str(value: object) -> str | None:
    if value is None:
        return None
    return str(value)


SENSOR_DESCRIPTIONS: tuple[SVOTCSensorDescription, ...] = (
    SVOTCSensorDescription(
        key="virtual_outdoor_temperature",
        translation_key="virtual_outdoor_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
)

DATA_SENSOR_DESCRIPTIONS: tuple[SVOTCDataSensorDescription, ...] = (
    SVOTCDataSensorDescription(
        key="status",
        translation_key="status",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_as_str,
    ),
    SVOTCDataSensorDescription(
        key="reason_code",
        translation_key="reason_code",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_as_str,
    ),
    SVOTCDataSensorDescription(
        key="effective_mode",
        translation_key="effective_mode",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_as_str,
    ),
    SVOTCDataSensorDescription(
        key="current_price",
        translation_key="current_price",
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement="SEK/kWh",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_as_float,
    ),
    SVOTCDataSensorDescription(
        key="p70",
        translation_key="price_p70",
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement="SEK/kWh",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_as_float,
    ),
    SVOTCDataSensorDescription(
        key="dynamic_target_temperature",
        translation_key="dynamic_target_temperature",
        entity_category=EntityCategory.DIAGNOSTIC,
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_as_float,
    ),
)

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
    entities: list[SensorEntity] = [
        SVOTCSensorEntity(coordinator, entry, description)
        for description in SENSOR_DESCRIPTIONS
    ]
    entities.extend(
        SVOTCDataSensorEntity(coordinator, entry, description)
        for description in DATA_SENSOR_DESCRIPTIONS
    )
    async_add_entities(entities)


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
        data = dict(self.coordinator.data)
        data["mode"] = self.coordinator.values.get("mode")
        return data

    @property
    def available(self) -> bool:
        """Return entity availability."""
        return self.coordinator.last_update_success

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        value = self.coordinator.data.get(self.entity_description.key)
        _LOGGER.debug(
            "Coordinator update for %s: %s", self.entity_description.key, value
        )
        super()._handle_coordinator_update()


class SVOTCDataSensorEntity(CoordinatorEntity, SensorEntity):
    """Representation of a SVOTC data sensor."""

    _attr_should_poll = False

    def __init__(
        self,
        coordinator: SVOTCCoordinator,
        entry: ConfigEntry,
        description: SVOTCDataSensorDescription,
    ) -> None:
        """Initialize the data sensor."""
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
    def native_value(self) -> float | str | None:
        """Return the sensor value."""
        value = self.coordinator.data.get(self.entity_description.key)
        return self.entity_description.value_fn(value)

    @property
    def available(self) -> bool:
        """Return entity availability."""
        return self.coordinator.last_update_success
