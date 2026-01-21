"""Entity ID migration helpers for SVOTC."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .const import DOMAIN
from .number import NUMBER_OBJECT_IDS, NUMBER_UNIQUE_ID_KEYS
from .select import SELECT_OBJECT_IDS, SELECT_UNIQUE_ID_KEYS
from .sensor import SENSOR_OBJECT_IDS, SENSOR_UNIQUE_ID_KEYS


PLATFORM_OBJECT_IDS: dict[Platform, dict[str, str]] = {
    Platform.NUMBER: NUMBER_OBJECT_IDS,
    Platform.SELECT: SELECT_OBJECT_IDS,
    Platform.SENSOR: SENSOR_OBJECT_IDS,
}

PLATFORM_UNIQUE_ID_KEYS: dict[Platform, dict[str, str]] = {
    Platform.NUMBER: NUMBER_UNIQUE_ID_KEYS,
    Platform.SELECT: SELECT_UNIQUE_ID_KEYS,
    Platform.SENSOR: SENSOR_UNIQUE_ID_KEYS,
}


def _legacy_object_ids(desired_object_id: str) -> set[str]:
    return {
        f"{DOMAIN}_{desired_object_id}",
        f"{DOMAIN}_{DOMAIN}_{desired_object_id}",
    }


def _legacy_sensor_object_ids(desired_object_id: str) -> set[str]:
    return {
        DOMAIN,
        f"{DOMAIN}_{DOMAIN}",
        f"{DOMAIN}_{desired_object_id}",
        f"{DOMAIN}_{DOMAIN}_{desired_object_id}",
    }


def _matches_legacy_entity_id(
    entity_id: str,
    platform: Platform,
    desired_object_id: str,
) -> bool:
    object_id = entity_id.split(".", 1)[1]
    if platform == Platform.SENSOR:
        return object_id in _legacy_sensor_object_ids(desired_object_id)
    return object_id in _legacy_object_ids(desired_object_id)


async def async_migrate_entity_ids(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Migrate duplicated entity IDs to shorter defaults."""
    registry = er.async_get(hass)
    for platform, object_ids in PLATFORM_OBJECT_IDS.items():
        unique_id_keys = PLATFORM_UNIQUE_ID_KEYS[platform]
        for key, desired_object_id in object_ids.items():
            new_unique_id = f"{entry.entry_id}_{key}"
            entity_id = registry.async_get_entity_id(platform, DOMAIN, new_unique_id)
            if entity_id is None:
                legacy_unique_id = unique_id_keys[key]
                legacy_entity_id = registry.async_get_entity_id(
                    platform, DOMAIN, legacy_unique_id
                )
                if legacy_entity_id is not None:
                    registry.async_update_entity(
                        legacy_entity_id,
                        new_unique_id=new_unique_id,
                    )
                    entity_id = legacy_entity_id
            if entity_id is None:
                continue
            if not _matches_legacy_entity_id(entity_id, platform, desired_object_id):
                continue
            platform_name = platform.value
            new_entity_id = f"{platform_name}.{desired_object_id}"
            if registry.async_get(new_entity_id) is not None:
                continue
            registry.async_update_entity(entity_id, new_entity_id=new_entity_id)
