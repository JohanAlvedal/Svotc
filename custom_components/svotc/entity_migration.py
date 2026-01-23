"""Entity ID migration helpers for SVOTC."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .const import DOMAIN
from .number import NUMBER_OBJECT_IDS
from .select import SELECT_OBJECT_IDS
from .sensor import SENSOR_OBJECT_IDS

# Entity domain ("sensor"/"number"/"select") -> key -> desired object_id
DOMAIN_OBJECT_IDS: dict[str, dict[str, str]] = {
    "number": NUMBER_OBJECT_IDS,
    "select": SELECT_OBJECT_IDS,
    "sensor": SENSOR_OBJECT_IDS,
}


def _split_entity_id(entity_id: str) -> tuple[str, str] | None:
    """Split 'sensor.foo' into ('sensor', 'foo')."""
    if "." not in entity_id:
        return None
    ent_domain, object_id = entity_id.split(".", 1)
    return ent_domain, object_id


def _extract_key_from_bad_object_id(object_id: str, entry: ConfigEntry) -> str | None:
    """Extract the entity key from known bad auto-generated object_id patterns."""
    # Example: svotc_<entryid>_virtual_outdoor_temperature
    prefix_entry = f"{DOMAIN}_{entry.entry_id}_"
    if object_id.startswith(prefix_entry):
        return object_id[len(prefix_entry) :]

    # Example: svotc_svotc_virtual_outdoor_temperature
    prefix_double = f"{DOMAIN}_{DOMAIN}_"
    if object_id.startswith(prefix_double):
        return object_id[len(prefix_double) :]

    return None


async def async_migrate_entity_ids(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Migrate bad auto-generated SVOTC entity_ids to clean defaults."""
    registry = er.async_get(hass)

    # All entities tied to this config entry
    entries = er.async_entries_for_config_entry(registry, entry.entry_id)

    for reg_entry in entries:
        # Only touch entities created by this integration
        if reg_entry.platform != DOMAIN:
            continue

        parsed = _split_entity_id(reg_entry.entity_id)
        if parsed is None:
            continue

        ent_domain, object_id = parsed

        # Only rename the known bad patterns
        key = _extract_key_from_bad_object_id(object_id, entry)
        if key is None:
            continue

        key_map = DOMAIN_OBJECT_IDS.get(ent_domain)
        if not key_map:
            continue

        desired_object_id = key_map.get(key)
        if not desired_object_id:
            continue

        new_entity_id = f"{ent_domain}.{desired_object_id}"

        # Only rename if target is free
        if registry.async_get(new_entity_id) is not None:
            continue

        registry.async_update_entity(reg_entry.entity_id, new_entity_id=new_entity_id)
