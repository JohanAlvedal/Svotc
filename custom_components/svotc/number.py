"""Number entities for SVOTC."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.number import (
    NumberEntity,
    NumberEntityDescription,
    NumberMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import (
    DEFAULT_BRAKE_AGGRESSIVENESS,
    DEFAULT_COMFORT_TEMPERATURE,
    DEFAULT_HEAT_AGGRESSIVENESS,
    DEFAULT_VACATION_TEMPERATURE,
    DOMAIN,
)
from .coordinator import SVOTCCoordinator


@dataclass(frozen=True, kw_only=True)
class SVOTCNumberDescription(NumberEntityDescription):
    """Describe a SVOTC number entity."""

    key: str
    default: float


NUMBER_DESCRIPTIONS: tuple[SVOTCNumberDescription, ...] = (
    SVOTCNumberDescription(
        key="brake_aggressiveness",
        translation_key="brake_aggressiveness",
        default=DEFAULT_BRAKE_AGGRESSIVENESS,
        native_min_value=0,
        native_max_value=5,
        native_step=1,
    ),
    SVOTCNumberDescription(
        key="heat_aggressiveness",
        translation_key="heat_aggressiveness",
        default=DEFAULT_HEAT_AGGRESSIVENESS,
        native_min_value=0,
        native_max_value=5,
        native_step=1,
    ),
    SVOTCNumberDescription(
        key="comfort_temperature",
        translation_key="comfort_temperature",
        default=DEFAULT_COMFORT_TEMPERATURE,
        native_min_value=5,
        native_max_value=30,
        native_step=0.5,
    ),
    SVOTCNumberDescription(
        key="vacation_temperature",
        translation_key="vacation_temperature",
        default=DEFAULT_VACATION_TEMPERATURE,
        native_min_value=5,
        native_max_value=30,
        native_step=0.5,
    ),
)

# Keep entity_id readable and stable: number.svotc_<key>
NUMBER_OBJECT_IDS: dict[str, str] = {
    "brake_aggressiveness": f"{DOMAIN}_brake_aggressiveness",
    "heat_aggressiveness": f"{DOMAIN}_heat_aggressiveness",
    "comfort_temperature": f"{DOMAIN}_comfort_temperature",
    "vacation_temperature": f"{DOMAIN}_vacation_temperature",
}

# Legacy unique_ids used before switching to per-entry unique IDs.
# Used by entity_id migration to find and migrate older entities.
NUMBER_UNIQUE_ID_KEYS: dict[str, str] = {
    "brake_aggressiveness": f"{DOMAIN}_brake",
    "heat_aggressiveness": f"{DOMAIN}_heat",
    "comfort_temperature": f"{DOMAIN}_comfort",
    "vacation_temperature": f"{DOMAIN}_vacation",
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up SVOTC number entities."""
    coordinator: SVOTCCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        SVOTCNumberEntity(coordinator, entry, description)
        for description in NUMBER_DESCRIPTIONS
    )


class SVOTCNumberEntity(NumberEntity, RestoreEntity):
    """Representation of a SVOTC number entity."""

    _attr_mode = NumberMode.BOX

    def __init__(
        self,
        coordinator: SVOTCCoordinator,
        entry: ConfigEntry,
        description: SVOTCNumberDescription,
    ) -> None:
        """Initialize the SVOTC number entity."""
        self.entity_description = description
        self.coordinator = coordinator

        # Unique per config entry + key (supports multiple entries safely)
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"

        # Desired entity_id: number.svotc_<key> (no entry_id in object_id)
        self._attr_suggested_object_id = NUMBER_OBJECT_IDS.get(
            description.key, f"{DOMAIN}_{description.key}"
        )

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="SVOTC",
        )
        if description.key in {"brake_aggressiveness", "heat_aggressiveness"}:
            self._attr_mode = NumberMode.SLIDER
        else:
            self._attr_mode = NumberMode.BOX

    @property
    def native_value(self) -> float:
        """Return the current value."""
        return float(
            self.coordinator.values.get(
                self.entity_description.key, self.entity_description.default
            )
        )

    async def async_added_to_hass(self) -> None:
        """Restore value on startup."""
        await super().async_added_to_hass()
        state = await self.async_get_last_state()
        if state is None:
            return
        try:
            restored = float(state.state)
        except ValueError:
            return
        await self.coordinator.async_set_value(self.entity_description.key, restored)

    async def async_set_native_value(self, value: float) -> None:
        """Update the value."""
        await self.coordinator.async_set_value(self.entity_description.key, value)
