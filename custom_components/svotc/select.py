"""Select entity for SVOTC."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import DEFAULT_MODE, DOMAIN, MODE_OPTIONS
from .coordinator import SVOTCCoordinator

SELECT_OBJECT_IDS: dict[str, str] = {
    "mode": "mode",
}

SELECT_UNIQUE_ID_KEYS: dict[str, str] = {
    "mode": f"{DOMAIN}_mode",
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up SVOTC select entities."""
    coordinator: SVOTCCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([SVOTCModeSelect(coordinator, entry)])


class SVOTCModeSelect(SelectEntity, RestoreEntity):
    """Representation of the SVOTC mode select."""

    _attr_options = MODE_OPTIONS
    _attr_translation_key = "mode"

    def __init__(self, coordinator: SVOTCCoordinator, entry: ConfigEntry) -> None:
        """Initialize the mode select."""
        self.coordinator = coordinator
        self._attr_unique_id = f"{entry.entry_id}_mode"
        self._attr_suggested_object_id = SELECT_OBJECT_IDS["mode"]
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="SVOTC",
        )

    @property
    def current_option(self) -> str:
        """Return the current selected mode."""
        return str(self.coordinator.values.get("mode", DEFAULT_MODE))

    async def async_added_to_hass(self) -> None:
        """Restore value on startup."""
        await super().async_added_to_hass()
        state = await self.async_get_last_state()
        if state is None or state.state not in MODE_OPTIONS:
            return
        await self.coordinator.async_set_value("mode", state.state)

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        await self.coordinator.async_set_value("mode", option)
