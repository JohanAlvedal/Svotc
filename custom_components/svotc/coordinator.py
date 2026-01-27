"""Data coordinator for SVOTC."""

from __future__ import annotations

from datetime import datetime, time, timedelta
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
from .forecast import min_outdoor_next_12h
from .mapping import brake_offset, heat_offset, max_abs_offset
from .control import clamp, compute_price_offset, smooth_asymmetric, update_comfort_pi
from .prices import (
    classify_price,
    extract_price_entries,
    price_percentile,
    price_percentiles,
    select_current_price,
)
from .ramp import max_delta_per_update, ramp_offset

_LOGGER = logging.getLogger(__name__)

_GRACE_PERIOD = timedelta(seconds=60)
_GLITCH_HOLD = timedelta(seconds=60)
_TOMORROW_WARNING_AFTER = timedelta(minutes=10)
_COMFORT_DEADBAND_C = 0.2
_COMFORT_KP = -1.1
_COMFORT_KI = -0.0006
_COMFORT_I_MIN = -4.0
_COMFORT_I_MAX = 4.0
_COMFORT_FILTER_TAU_S = 300.0
_PRICE_DECAY_TAU_S = 900.0
_PRICE_BIAS_THRESHOLD_C = 0.2
_HEAT_WINDOW_C = 1.2
_BRAKE_REDUCTION_MAX = 0.8
_BRAKE_REDUCTION_MIN = 0.2
_BRAKE_EXIT_PERCENTILE = 0.60
_BRAKE_EXIT_RATIO = 0.6
_BRAKE_HOLD_TIME = timedelta(minutes=40)
_BRAKE_HOLD_MIN_C = 0.3
_BRAKE_STRONG_RATIO = 0.8


def _brake_reduction_strength(level: int) -> float:
    """Return a brake reduction strength based on aggressiveness."""
    scaled = _BRAKE_REDUCTION_MAX - (level / 5) * (
        _BRAKE_REDUCTION_MAX - _BRAKE_REDUCTION_MIN
    )
    return clamp(scaled, _BRAKE_REDUCTION_MIN, _BRAKE_REDUCTION_MAX)


def _should_require_tomorrow(now: datetime) -> bool:
    """Return True when tomorrow prices should be available locally."""
    local_time = dt_util.as_local(now).time()
    return local_time >= time(13, 45)


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
        self._last_offset_source: str = "memory"
        self._last_price_state: str | None = None
        self._last_price_state_changed: datetime | None = None
        self._last_today_missing: bool | None = None
        self._last_required_missing: bool | None = None
        self._tomorrow_issue_since: datetime | None = None
        self._tomorrow_issue_warned: bool = False
        self._comfort_integrator: float = 0.0
        self._comfort_filtered_error: float | None = None
        self._last_control_time: datetime | None = None
        self._price_offset_smoothed: float | None = None
        self._brake_active: bool = False
        self._brake_hold_until: datetime | None = None

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
        _LOGGER.debug(
            "Coordinator refresh start (interval=%s).", self.update_interval
        )
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
        p60 = price_percentile(price_series, _BRAKE_EXIT_PERCENTILE)
        self._log_today_missing(now, today_missing)
        if price_entity_tomorrow and _should_require_tomorrow(now):
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
        if (
            price_entity_tomorrow
            and not tomorrow_valid
            and _should_require_tomorrow(now)
        ):
            missing_inputs.append("price_tomorrow")

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
                _LOGGER.debug(
                    "Coordinator refresh end: holding last output due to temporary missing inputs."
                )
                held = dict(self._last_output)
                held["status"] = "Holding (sensor glitch)"
                held["reason_code"] = "TEMP_GLITCH_HOLD"
                return held

        if critical_missing and not in_grace:
            _LOGGER.debug(
                "Coordinator refresh end: missing inputs (%s).",
                ", ".join(missing_inputs) if missing_inputs else "unknown",
            )
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
                "comfort_offset_c": 0.0,
                "price_offset_c": 0.0,
                "effective_price_offset_c": 0.0,
                "requested_offset_c": 0.0,
                "applied_offset_c": offset,
                "effective_mode": "off" if mode == "Off" else "neutral",
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
            return result

        if in_grace and critical_missing:
            _LOGGER.debug(
                "Coordinator refresh end: startup grace with missing inputs (%s).",
                ", ".join(missing_inputs) if missing_inputs else "unknown",
            )
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
                "comfort_offset_c": 0.0,
                "price_offset_c": 0.0,
                "effective_price_offset_c": 0.0,
                "requested_offset_c": 0.0,
                "applied_offset_c": offset,
                "effective_mode": "off" if mode == "Off" else "neutral",
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
            return result

        dt_seconds = (
            (now - self._last_control_time).total_seconds()
            if self._last_control_time is not None
            else self.update_interval.total_seconds()
        )
        self._last_control_time = now
        brake_aggressiveness = int(
            self.values.get("brake_aggressiveness", DEFAULT_BRAKE_AGGRESSIVENESS)
        )
        heat_aggressiveness = int(
            self.values.get("heat_aggressiveness", DEFAULT_HEAT_AGGRESSIVENESS)
        )
        max_brake_offset = brake_offset(brake_aggressiveness)
        max_heat_offset = abs(heat_offset(heat_aggressiveness))
        max_cool_offset = max_brake_offset
        price_offset_raw, price_ratio = compute_price_offset(
            current_price, p30, p70, max_brake_offset
        )
        brake_active = self._brake_active
        if current_price is None or p70 is None:
            brake_active = False
        else:
            if price_class == "expensive" or current_price >= p70:
                brake_active = True
            elif brake_active:
                exit_threshold = p60 if p60 is not None else p30
                if (
                    exit_threshold is not None
                    and current_price <= exit_threshold
                ) or (price_ratio is not None and price_ratio <= _BRAKE_EXIT_RATIO):
                    brake_active = False
        if self._brake_active and not brake_active:
            self._brake_hold_until = now + _BRAKE_HOLD_TIME
        if brake_active:
            self._brake_hold_until = None
        hold_remaining = 0.0
        if (
            not brake_active
            and self._brake_hold_until is not None
            and now < self._brake_hold_until
        ):
            hold_remaining = (self._brake_hold_until - now).total_seconds()
            price_offset_raw = max(price_offset_raw, _BRAKE_HOLD_MIN_C)
        price_offset = smooth_asymmetric(
            price_offset_raw,
            self._price_offset_smoothed,
            dt_seconds,
            _PRICE_DECAY_TAU_S,
        )
        self._price_offset_smoothed = price_offset
        self._brake_active = brake_active

        if mode == "Off" or indoor_temp is None:
            self._comfort_integrator = 0.0
            self._comfort_filtered_error = 0.0
            comfort_offset = 0.0
            error_c = 0.0
        else:
            error_c = float(dynamic_target) - indoor_temp
            strong_brake = (
                brake_active and price_offset >= max_brake_offset * _BRAKE_STRONG_RATIO
            )
            if strong_brake:
                self._comfort_integrator *= 0.9
            ki_scale = 0.2 if brake_active else 1.0
            comfort_result = update_comfort_pi(
                error_c=error_c,
                integrator=self._comfort_integrator,
                filtered_error=self._comfort_filtered_error,
                dt_seconds=dt_seconds,
                kp=_COMFORT_KP,
                ki=_COMFORT_KI * ki_scale,
                i_min=_COMFORT_I_MIN,
                i_max=_COMFORT_I_MAX,
                deadband_c=_COMFORT_DEADBAND_C,
                max_cool_c=max_cool_offset,
                max_heat_c=max_heat_offset,
                integrate=not strong_brake,
                filter_time_constant_seconds=_COMFORT_FILTER_TAU_S,
            )
            self._comfort_integrator = comfort_result.integrator
            self._comfort_filtered_error = comfort_result.filtered_error
            comfort_offset = comfort_result.offset

        heat_need_factor = clamp(
            (error_c - _COMFORT_DEADBAND_C) / _HEAT_WINDOW_C, 0.0, 1.0
        )
        brake_reduction_strength = _brake_reduction_strength(brake_aggressiveness)
        effective_price_offset = price_offset * (
            1 - heat_need_factor * brake_reduction_strength
        )

        requested_offset = comfort_offset + effective_price_offset
        if mode == "Off":
            requested_offset = 0.0
            effective_price_offset = 0.0
            price_offset = 0.0

        limiting_comfort = (
            mode != "Off"
            and price_offset > 0.0
            and effective_price_offset < price_offset
            and error_c > _COMFORT_DEADBAND_C
        )
        price_bias_active = price_offset > _PRICE_BIAS_THRESHOLD_C
        net_braking = requested_offset > _PRICE_BIAS_THRESHOLD_C and price_bias_active
        net_heating = requested_offset < -_PRICE_BIAS_THRESHOLD_C

        if mode == "Off":
            status = "Off"
            reason_code = "OFF"
            effective_mode = "off"
        elif limiting_comfort:
            status = "Braking (limiting comfort)"
            reason_code = "PRICE_LIMITING_COMFORT"
            effective_mode = "limiting_comfort"
        elif net_braking:
            if current_price is not None and p70 is not None and current_price >= p70:
                status = "Braking (expensive price)"
                reason_code = "PRICE_BRAKE"
            else:
                status = "Braking (elevated price)"
                reason_code = "PRICE_ELEVATED"
            effective_mode = "brake"
        elif requested_offset > _PRICE_BIAS_THRESHOLD_C:
            status = "Smart (comfort control)"
            reason_code = "COMFORT_PI"
            effective_mode = "comfort"
        elif net_heating:
            status = "Smart (comfort control)"
            reason_code = "COMFORT_PI"
            effective_mode = "boost" if price_class == "cheap" else "comfort"
        else:
            status = "Neutral"
            reason_code = "NEUTRAL"
            effective_mode = "neutral"

        if mode != "Off":
            if price_bias_active:
                price_state = "brake"
            elif price_class == "cheap":
                price_state = "boost"
            else:
                price_state = "neutral"
        else:
            price_state = None

        _LOGGER.debug(
            "Comfort PI: target=%.2f, indoor=%.2f, error=%.3f, P=%.3f, I=%.3f, offset=%.3f.",
            float(dynamic_target),
            indoor_temp if indoor_temp is not None else float("nan"),
            (float(dynamic_target) - indoor_temp) if indoor_temp is not None else 0.0,
            _COMFORT_KP * (self._comfort_filtered_error or 0.0),
            self._comfort_integrator,
            comfort_offset,
        )
        _LOGGER.debug(
            "Price bias: current=%.3f, p30=%s, p70=%s, ratio=%s, offset=%.3f, brake=%s, hold_remaining=%.0fs.",
            current_price if current_price is not None else float("nan"),
            f"{p30:.3f}" if isinstance(p30, (int, float)) else "None",
            f"{p70:.3f}" if isinstance(p70, (int, float)) else "None",
            f"{price_ratio:.3f}" if isinstance(price_ratio, (int, float)) else "None",
            price_offset,
            brake_active,
            hold_remaining,
        )
        _LOGGER.debug(
            "Requested offset=%.3f (price_offset=%.3f, effective_price_offset=%.3f, comfort_offset=%.3f).",
            requested_offset,
            price_offset,
            effective_price_offset,
            comfort_offset,
        )

        max_delta = max_delta_per_update(max_abs_offset())
        last_offset = self._last_offset
        _LOGGER.debug(
            "Using last_applied_offset_c=%.3f (source=%s).",
            last_offset,
            self._last_offset_source,
        )
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

        if price_state is not None:
            if price_state != self._last_price_state:
                self._last_price_state = price_state
                self._last_price_state_changed = now

        result = {
            "indoor_temperature": indoor_temp,
            "outdoor_temperature": outdoor_temp,
            "virtual_outdoor_temperature": virtual_outdoor,
            "offset": offset,
            "requested_offset": requested_offset,
            "applied_offset": offset,
            "comfort_offset_c": comfort_offset,
            "price_offset_c": price_offset,
            "effective_price_offset_c": effective_price_offset,
            "requested_offset_c": requested_offset,
            "applied_offset_c": offset,
            "effective_mode": effective_mode,
            "ramp_limited": ramp_limited,
            "max_delta_per_step": max_delta,
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
            "price_state": price_state,
            "p30": p30,
            "p70": p70,
            "missing_inputs": missing_inputs,
        }
        previous_virtual = (
            self._last_output.get("virtual_outdoor_temperature")
            if self._last_output
            else None
        )
        _LOGGER.debug(
            "Computed virtual_outdoor_temperature %s -> %s (requested_offset=%.3f, applied_offset=%.3f, ramp_limited=%s).",
            f"{previous_virtual:.3f}" if isinstance(previous_virtual, (int, float)) else "None",
            f"{virtual_outdoor:.3f}" if isinstance(virtual_outdoor, (int, float)) else "None",
            requested_offset,
            offset,
            ramp_limited,
        )
        self._last_output = result
        self._last_offset = offset
        self._last_offset_source = "memory"
        _LOGGER.debug("Coordinator refresh end: update successful.")
        return {
            **result,
        }
