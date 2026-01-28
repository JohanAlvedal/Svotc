"""Constants for the SVOTC integration."""

DOMAIN = "svotc"

CONF_INDOOR_TEMPERATURE = "indoor_temperature"
CONF_OUTDOOR_TEMPERATURE = "outdoor_temperature"
CONF_PRICE_ENTITY = "price_entity"
CONF_PRICE_ENTITY_TODAY = "price_entity_today"
CONF_PRICE_ENTITY_TOMORROW = "price_entity_tomorrow"
CONF_WEATHER_ENTITY = "weather_entity"

DEFAULT_BRAKE_AGGRESSIVENESS = 3
DEFAULT_HEAT_AGGRESSIVENESS = 0
DEFAULT_COMFORT_TEMPERATURE = 21.0
DEFAULT_VACATION_TEMPERATURE = 17.0
DEFAULT_MODE = "Off"

MODE_OPTIONS = ["Off", "Smart", "Vacation"]

# Deterministic object_id mapping for coordinator data keys.
SENSOR_OBJECT_IDS: dict[str, str] = {
    "status": "svotc_status",
    "reason_code": "svotc_reason_code",
    "effective_mode": "svotc_effective_mode",
    "current_price": "svotc_current_price",
    "p70": "svotc_price_p70",
    "dynamic_target_temperature": "svotc_dynamic_target_temperature",
    "tomorrow_available": "svotc_tomorrow_available",
    "virtual_outdoor_temperature": "svotc_virtual_outdoor_temperature",
}
