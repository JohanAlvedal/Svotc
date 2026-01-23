"""Data coordinator for SVOTC."""

from __future__ import annotations

from datetime import datetime, timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from .const import (
    CONF_INDOOR_TEMPERATURE,
    CONF_OUTDOOR_TEMPERATURE,
    CONF_PRICE_ENTITY,
    CONF_PRICE_ENTITY_TODAY,
    CONF_PRICE_ENTITY_TOMORROW,
    CONF_WEATHER_ENTITY,
    DEFAULT_BRAKE_AGGRESSIVENESS,
    DEFAULT_COMFORT_TEMPERATURE,
    DEFAULT_HEAT_AGGRESSIVENESS,
    DEFAULT_MODE,
    DEFAULT_VACATION_TEMPERATURE,
    DOMAIN,
)
from .decision import DecisionInput, decide
from .forecast import min_outdoor_next_12h
from .mapping import max_abs_offset
from .prices import (
    classify_price,
    extract_price_entries,
    price_percentiles,
    select_current_price,
)
from .ramp import max_delta_per_update, ramp_offset

_LOGGER = logging.getLogger(__name__)

_GRACE_PERIOD = timedelta(seconds=60)
_GLITCH_HOLD = timedelta(seconds=60)
_TOMORROW_WARNING_AFTER = timedelta(minutes=10)


class SVOTCCoordinator(DataUpdateCoordinator[dict[str, object]]):
    """Coordinate SVOTC state updates."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=60),
        )
        self.entry = entry
        self.values: dict[str, object] = {
            "brake_aggressiveness": DEFAULT_BRAKE_AGGRESSIVENESS,
            "heat_aggressiveness": DEFAULT_HEAT_AGGRESSIVENESS,
            "comfort_temperature": DEFAULT_COMFORT_TEMPERATURE,
            "vacation_temperature": DEFAULT_VACATION_TEMPERATURE,
            "mode": DEFAULT_MODE,
        }
        self._start_time = dt_util.utcnow()
        self._last_complete_time: datetime | None = None
        self._last_output: dict[str, object] | None = None
        self._last_offset: float = 0.0
        self._last_price_state: str | None = None
        self._last_price_state_changed: datetime | None = None
        self._last_today_missing: bool | None = None
        self._last_required_missing: bool | None = None
        self._tomorrow_issue_since: datetime | None = None
        self._tomorrow_issue_warned: bool = False

    def _read_temperature(self, entity_id: str | None) -> float | None:
        """Read a temperature from a Home Assistant state."""
        if not entity_id:
            return None
        state = self.hass.states.get(entity_id)
        if state is None or state.state in ("unknown", "unavailable"):
            return None
        try:
            return float(state.state)
        except ValueError:
            return None

    def _read_state(self, entity_id: str | None) -> object | None:
        """Read a raw state for an entity."""
        if not entity_id:
            return None
        state = self.hass.states.get(entity_id)
        if state is None or state.state in ("unknown", "unavailable"):
            return None
        return state

    def _missing_reason(
        self,
        indoor: float | None,
        outdoor: float | None,
        price_available: bool,
        forecast_available: bool,
    ) -> str:
        """Return a reason code for missing critical inputs."""
        if indoor is None or outdoor is None:
            return "MISSING_INDOOR"
        if not price_available and not forecast_available:
            return "MISSING_BOTH"
        if not price_available:
            return "MISSING_PRICE"
        if not forecast_available:
            return "MISSING_FORECAST"
        return "MISSING_BOTH"

    def _log_today_missing(self, now: datetime, missing: bool) -> None:
        """Log transitions for missing today prices."""
        in_grace = now - self._start_time <= _GRACE_PERIOD
        if in_grace:
            self._last_today_missing = None
            return
        if missing and self._last_today_missing is not True:
            _LOGGER.warning("Price data for today is missing or empty.")
        self._last_today_missing = missing

    def _log_required_missing(
        self, now: datetime, missing: bool, details: list[str]
    ) -> None:
        """Log transitions for missing required inputs."""
        in_grace = now - self._start_time <= _GRACE_PERIOD
        if in_grace:
            self._last_required_missing = None
            return
        if missing and self._last_required_missing is not True:
            detail_text = ", ".join(details) if details else "unknown"
            _LOGGER.warning("Required inputs missing: %s.", detail_text)
        self._last_required_missing = missing

    def _log_tomorrow_issue(self, now: datetime, issue: bool) -> None:
        """Log issues with tomorrow prices with throttling."""
        if not issue:
            self._tomorrow_issue_since = None
            self._tomorrow_issue_warned = False
            return
        if self._tomorrow_issue_since is None:
            self._tomorrow_issue_since = now
            self._tomorrow_issue_warned = False
            _LOGGER.debug("Price data for tomorrow is missing or invalid.")
            return
        if (
            not self._tomorrow_issue_warned
            and now - self._tomorrow_issue_since > _TOMORROW_WARNING_AFTER
        ):
            _LOGGER.warning(
                "Price data for tomorrow has been missing or invalid for over 10 minutes."
            )
            self._tomorrow_issue_warned = True

    async def async_set_value(self, key: str, value: object) -> None:
        """Persist a value and refresh coordinator data."""
        self.values[key] = value
        await self.async_request_refresh()

    async def _async_update_data(self) -> dict[str, object]:
        """Fetch data for SVOTC sensors."""
        now = dt_util.utcnow()
        entry_data = {**self.entry.data, **self.entry.options}

        indoor_entity_id = entry_data.get(CONF_INDOOR_TEMPERATURE)
        outdoor_entity_id = entry_data.get(CONF_OUTDOOR_TEMPERATURE)
        price_entity_today = entry_data.get(CONF_PRICE_ENTITY_TODAY) or entry_data.get(
            CONF_PRICE_ENTITY
        )
        price_entity_tomorrow = entry_data.get(CONF_PRICE_ENTITY_TOMORROW)
        weather_entity_id = entry_data.get(CONF_WEATHER_ENTITY)

        indoor_temp = self._read_temperature(indoor_entity_id)
        outdoor_temp = self._read_temperature(outdoor_entity_id)
        price_today_state = self._read_state(price_entity_today)
        price_tomorrow_state = self._read_state(price_entity_tomorrow)
        # weather_state is no longer used for forecasts; forecasts are retrieved via service API.
        # weather_state = self._read_state(weather_entity_id)

        mode = self.values.get("mode", DEFAULT_MODE)

        if mode == "Vacation":
            dynamic_target = self.values.get(
                "vacation_temperature", DEFAULT_VACATION_TEMPERATURE
            )
        else:
            dynamic_target = self.values.get(
                "comfort_temperature", DEFAULT_COMFORT_TEMPERATURE
            )

        today_entries = extract_price_entries(price_today_state)
        tomorrow_entries = (
            extract_price_entries(price_tomorrow_state) if price_entity_tomorrow else []
        )
        tomorrow_valid = bool(tomorrow_entries)
        combined_entries = (
            today_entries + tomorrow_entries if tomorrow_valid else list(today_entries)
        )
        current_price = None
        if today_entries:
            current_price = select_current_price(today_entries, now)
        if current_price is None and tomorrow_valid:
            current_price = select_current_price(tomorrow_entries, now)
        price_series = [float(entry["price"]) for entry in combined_entries]
        today_missing = not today_entries
        if today_missing:
            current_price = None
        price_available = bool(today_entries) and current_price is not None
        price_class = classify_price(current_price, price_series)
        p30, p70 = price_percentiles(price_series)
        self._log_today_missing(now, today_missing)
        if price_entity_tomorrow:
            self._log_tomorrow_issue(now, not tomorrow_valid)

        forecast_min = None
        if weather_entity_id:
            forecast_min = await min_outdoor_next_12h(self.hass, weather_entity_id, now)
        forecast_available = forecast_min is not None

        missing_inputs: list[str] = []
        if indoor_entity_id and indoor_temp is None:
            missing_inputs.append("indoor_temperature")
        if outdoor_entity_id and outdoor_temp is None:
            missing_inputs.append("outdoor_temperature")
        if today_missing:
            missing_inputs.append("price_today")
        if current_price is None and not today_missing:
            missing_inputs.append("current_price")

        critical_missing = False
        if indoor_entity_id and indoor_temp is None:
            critical_missing = True
        if outdoor_entity_id and outdoor_temp is None:
            critical_missing = True
        if price_entity_today and not price_available:
            critical_missing = True
        if weather_entity_id and not forecast_available:
            critical_missing = True

        required_missing = False
        if indoor_entity_id and indoor_temp is None:
            required_missing = True
        if outdoor_entity_id and outdoor_temp is None:
            required_missing = True
        if price_entity_today and (today_missing or current_price is None):
            required_missing = True

        required_missing_details = list(missing_inputs)
        self._log_required_missing(now, required_missing, required_missing_details)

        if not critical_missing:
            self._last_complete_time = now

        in_grace = now - self._start_time <= _GRACE_PERIOD
        missing_duration = (
            now - self._last_complete_time
            if self._last_complete_time is not None
            else None
        )

        price_bypass = today_missing or current_price is None

        if critical_missing and not in_grace and self._last_output is not None and not price_bypass:
            if missing_duration is not None and missing_duration <= _GLITCH_HOLD:
                held = dict(self._last_output)
                held["status"] = "Holding (sensor glitch)"
                held["reason_code"] = "TEMP_GLITCH_HOLD"
                return held

        if critical_missing and not in_grace:
            if today_missing or current_price is None:
                reason_code = "MISSING_PRICE"
            else:
                reason_code = self._missing_reason(
                    indoor_temp, outdoor_temp, price_available, forecast_available
                )
            status = reason_code.replace("_", " ").title()
            last_offset = self._last_offset
            offset = 0.0
            virtual_outdoor = outdoor_temp if outdoor_temp is not None else None
            result = {
                "indoor_temperature": indoor_temp,
                "outdoor_temperature": outdoor_temp,
                "virtual_outdoor_temperature": virtual_outdoor,
                "offset": offset,
                "requested_offset": 0.0,
                "applied_offset": offset,
                "ramp_limited": False,
                "max_delta_per_step": max_delta_per_update(max_abs_offset()),
                "last_applied_offset": last_offset,
                "dynamic_target_temperature": dynamic_target,
                "status": status,
                "reason_code": reason_code,
                "price_entities_used": {
                    "today": price_entity_today,
                    "tomorrow": price_entity_tomorrow,
                },
                "prices_count_today": len(today_entries),
                "prices_count_tomorrow": len(tomorrow_entries) if tomorrow_valid else 0,
                "tomorrow_available": tomorrow_valid,
                "prices_count_total": len(price_series),
                "current_price": current_price,
                "price_state": None,
                "p30": p30,
                "p70": p70,
                "missing_inputs": missing_inputs,
            }
            self._last_output = result
            self._last_offset = offset
            return result

        if in_grace and critical_missing:
            offset = 0.0
            virtual_outdoor = outdoor_temp + offset if outdoor_temp is not None else None
            last_offset = self._last_offset
            if today_missing or current_price is None:
                reason_code = "MISSING_PRICE"
            else:
                reason_code = self._missing_reason(
                    indoor_temp, outdoor_temp, price_available, forecast_available
                )
            result = {
                "indoor_temperature": indoor_temp,
                "outdoor_temperature": outdoor_temp,
                "virtual_outdoor_temperature": virtual_outdoor,
                "offset": offset,
                "requested_offset": 0.0,
                "applied_offset": offset,
                "ramp_limited": False,
                "max_delta_per_step": max_delta_per_update(max_abs_offset()),
                "last_applied_offset": last_offset,
                "dynamic_target_temperature": dynamic_target,
                "status": "Startup grace",
                "reason_code": reason_code,
                "price_entities_used": {
                    "today": price_entity_today,
                    "tomorrow": price_entity_tomorrow,
                },
                "prices_count_today": len(today_entries),
                "prices_count_tomorrow": len(tomorrow_entries) if tomorrow_valid else 0,
                "tomorrow_available": tomorrow_valid,
                "prices_count_total": len(price_series),
                "current_price": current_price,
                "price_state": None,
                "p30": p30,
                "p70": p70,
                "missing_inputs": missing_inputs,
            }
            self._last_output = result
            self._last_offset = offset
            return result

        decision = decide(
            DecisionInput(
                mode=str(mode),
                indoor_temp=indoor_temp,
                outdoor_temp=outdoor_temp,
                dynamic_target=float(dynamic_target),
                brake_aggressiveness=int(
                    self.values.get("brake_aggressiveness", DEFAULT_BRAKE_AGGRESSIVENESS)
                ),
                heat_aggressiveness=int(
                    self.values.get("heat_aggressiveness", DEFAULT_HEAT_AGGRESSIVENESS)
                ),
                price_class=price_class,
                forecast_min_next_6h=forecast_min,
                price_available=price_available,
                forecast_available=forecast_available,
                now=now,
                last_price_state=self._last_price_state,
                last_price_state_changed=self._last_price_state_changed,
            )
        )

        max_delta = max_delta_per_update(max_abs_offset())
        requested_offset = decision.target_offset
        last_offset = self._last_offset
        ramped_offset = ramp_offset(last_offset, requested_offset, max_delta)
        ramp_limited = ramped_offset != requested_offset
        offset = ramped_offset
        virtual_outdoor = outdoor_temp + offset if outdoor_temp is not None else None
        if virtual_outdoor is not None:
            clamped_virtual = max(-25.0, min(25.0, virtual_outdoor))
            if clamped_virtual != virtual_outdoor:
                offset = clamped_virtual - outdoor_temp
                virtual_outdoor = clamped_virtual
                ramp_limited = True

        if decision.price_state is not None:
            if decision.price_state != self._last_price_state:
                self._last_price_state = decision.price_state
                self._last_price_state_changed = now

        result = {
            "indoor_temperature": indoor_temp,
            "outdoor_temperature": outdoor_temp,
            "virtual_outdoor_temperature": virtual_outdoor,
            "offset": offset,
            "requested_offset": requested_offset,
            "applied_offset": offset,
            "ramp_limited": ramp_limited,
            "max_delta_per_step": max_delta,
            "last_applied_offset": last_offset,
            "dynamic_target_temperature": dynamic_target,
            "status": decision.status,
            "reason_code": decision.reason_code,
            "price_entities_used": {
                "today": price_entity_today,
                "tomorrow": price_entity_tomorrow,
            },
            "prices_count_today": len(today_entries),
            "prices_count_tomorrow": len(tomorrow_entries) if tomorrow_valid else 0,
            "tomorrow_available": tomorrow_valid,
            "prices_count_total": len(price_series),
            "current_price": current_price,
            "price_state": decision.price_state,
            "p30": p30,
            "p70": p70,
            "missing_inputs": missing_inputs,
        }
        self._last_output = result
        self._last_offset = offset
        return {
            **result,
        }
