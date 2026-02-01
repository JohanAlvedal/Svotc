"""Decision logic for SVOTC."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from .control import BrakeDecision, clamp, compute_brake_target, smooth_asymmetric, update_comfort_pi
from .mapping import brake_offset, heat_offset

_DWELL_TIME = timedelta(minutes=30)

_COMFORT_DEADBAND_C = 0.2
_COMFORT_KP = -1.1
_COMFORT_KI = -0.0006
_COMFORT_I_MIN = -4.0
_COMFORT_I_MAX = 4.0
_COMFORT_FILTER_TAU_S = 300.0
_COMFORT_GUARD_MARGIN_C = 0.3

_PRICE_DECAY_TAU_S = 900.0
_PRICE_BIAS_THRESHOLD_C = 0.2

_HEAT_WINDOW_C = 1.2
_BRAKE_REDUCTION_MAX = 0.8
_BRAKE_REDUCTION_MIN = 0.2

_BRAKE_STRONG_RATIO = 0.8


@dataclass(frozen=True)
class DecisionInput:
    """Inputs required for the decision logic."""

    mode: str
    indoor_temp: float | None
    outdoor_temp: float | None
    dynamic_target: float
    brake_aggressiveness: int
    heat_aggressiveness: int
    current_price: float | None
    price_class: str | None
    p70: float | None
    p80: float | None
    price_available: bool
    forecast_available: bool
    now: datetime
    dt_seconds: float
    require_indoor: bool
    require_outdoor: bool
    require_price: bool
    require_forecast: bool


@dataclass(frozen=True)
class DecisionState:
    """State required to keep decision logic continuous across updates."""

    comfort_integrator: float
    comfort_filtered_error: float | None
    price_offset_smoothed: float | None
    brake_active: bool
    last_price_state: str | None
    last_price_state_changed: datetime | None


@dataclass(frozen=True)
class DecisionOutput:
    """Decision output values."""

    requested_offset: float
    reason_code: str
    status: str
    effective_mode: str
    price_state: str | None
    comfort_offset: float
    price_offset: float
    effective_price_offset: float
    brake_active: bool
    in_peak: bool
    limiting_comfort: bool
    price_reason_code: str | None
    price_bias_active: bool
    comfort_integrator: float
    comfort_filtered_error: float | None
    price_offset_smoothed: float | None
    last_price_state: str | None
    last_price_state_changed: datetime | None


def _brake_reduction_strength(level: int) -> float:
    """Return a brake reduction strength based on aggressiveness."""
    scaled = _BRAKE_REDUCTION_MAX - (level / 5) * (
        _BRAKE_REDUCTION_MAX - _BRAKE_REDUCTION_MIN
    )
    return clamp(scaled, _BRAKE_REDUCTION_MIN, _BRAKE_REDUCTION_MAX)


def _missing_reason(inputs: DecisionInput) -> str | None:
    """Return a reason code for missing critical inputs."""
    if inputs.require_indoor and inputs.indoor_temp is None:
        return "MISSING_INDOOR"
    if inputs.require_outdoor and inputs.outdoor_temp is None:
        return "MISSING_INDOOR"
    if inputs.require_price and not inputs.price_available:
        if inputs.require_forecast and not inputs.forecast_available:
            return "MISSING_BOTH"
        return "MISSING_PRICE"
    if inputs.require_forecast and not inputs.forecast_available:
        return "MISSING_FORECAST"
    return None


def _apply_price_dwell(
    new_state: str,
    last_state: str | None,
    last_changed: datetime | None,
    now: datetime,
) -> str:
    """Apply dwell time for price-driven state changes."""
    if last_state is None or last_state == new_state:
        return new_state
    if last_changed is None:
        return new_state
    if now - last_changed < _DWELL_TIME:
        return last_state
    return new_state


def decide(inputs: DecisionInput, state: DecisionState) -> DecisionOutput:
    """Return the decision for the current update cycle."""
    missing_reason = _missing_reason(inputs)
    if missing_reason is not None:
        status = missing_reason.replace("_", " ").title()
        return DecisionOutput(
            requested_offset=0.0,
            reason_code=missing_reason,
            status=status,
            effective_mode="off" if inputs.mode == "Off" else "neutral",
            price_state=None,
            comfort_offset=0.0,
            price_offset=0.0,
            effective_price_offset=0.0,
            brake_active=state.brake_active,
            in_peak=False,
            limiting_comfort=False,
            price_reason_code=None,
            price_bias_active=False,
            comfort_integrator=state.comfort_integrator,
            comfort_filtered_error=state.comfort_filtered_error,
            price_offset_smoothed=state.price_offset_smoothed,
            last_price_state=state.last_price_state,
            last_price_state_changed=state.last_price_state_changed,
        )

    heat_enabled = inputs.heat_aggressiveness > 0
    max_brake_offset = brake_offset(inputs.brake_aggressiveness)
    max_heat_offset = abs(heat_offset(inputs.heat_aggressiveness)) if heat_enabled else 0.0
    max_cool_offset = max_brake_offset

    raw_price_state: str | None = None
    if inputs.mode != "Off":
        if inputs.price_class == "expensive":
            raw_price_state = "brake"
        elif inputs.price_class == "cheap" and heat_enabled:
            raw_price_state = "boost"
        else:
            raw_price_state = "neutral"

    price_state = raw_price_state
    last_price_state = state.last_price_state
    last_price_state_changed = state.last_price_state_changed
    if raw_price_state is not None:
        price_state = _apply_price_dwell(
            raw_price_state,
            state.last_price_state,
            state.last_price_state_changed,
            inputs.now,
        )
        if price_state != state.last_price_state:
            last_price_state = price_state
            last_price_state_changed = inputs.now

    comfort_guard_active = (
        inputs.mode != "Off"
        and inputs.indoor_temp is not None
        and inputs.indoor_temp <= (inputs.dynamic_target + _COMFORT_GUARD_MARGIN_C)
    )

    if price_state == "brake":
        brake_decision = compute_brake_target(
            current_price=inputs.current_price,
            p70=inputs.p70,
            p80=inputs.p80,
            max_brake_offset=max_brake_offset,
            brake_active=state.brake_active,
            last_offset=state.price_offset_smoothed,
            comfort_guard_active=comfort_guard_active,
        )
    else:
        brake_decision = BrakeDecision(
            target_offset=0.0,
            brake_active=False,
            in_peak=False,
            reason_code=None,
            limited_by_comfort=False,
        )

    price_offset = smooth_asymmetric(
        brake_decision.target_offset,
        state.price_offset_smoothed,
        inputs.dt_seconds,
        _PRICE_DECAY_TAU_S,
    )
    price_offset_smoothed = price_offset
    brake_active = brake_decision.brake_active if price_state == "brake" else False
    in_peak = brake_decision.in_peak if price_state == "brake" else False
    limiting_comfort = (
        brake_decision.limited_by_comfort if price_state == "brake" else False
    )
    price_reason_code = brake_decision.reason_code if price_state == "brake" else None

    if inputs.mode == "Off" or inputs.indoor_temp is None:
        comfort_integrator = 0.0
        comfort_filtered_error = 0.0
        comfort_offset = 0.0
        error_c = 0.0
    else:
        error_c = float(inputs.dynamic_target) - inputs.indoor_temp
        comfort_integrator = state.comfort_integrator
        if brake_active and (price_offset >= max_brake_offset * _BRAKE_STRONG_RATIO):
            comfort_integrator *= 0.9

        ki_scale = 0.2 if brake_active else 1.0

        comfort_result = update_comfort_pi(
            error_c=error_c,
            integrator=comfort_integrator,
            filtered_error=state.comfort_filtered_error,
            dt_seconds=inputs.dt_seconds,
            kp=_COMFORT_KP,
            ki=_COMFORT_KI * ki_scale,
            i_min=_COMFORT_I_MIN,
            i_max=_COMFORT_I_MAX,
            deadband_c=_COMFORT_DEADBAND_C,
            max_cool_c=max_cool_offset,
            max_heat_c=max_heat_offset,
            integrate=not (brake_active and price_offset >= max_brake_offset * _BRAKE_STRONG_RATIO),
            filter_time_constant_seconds=_COMFORT_FILTER_TAU_S,
        )
        comfort_integrator = comfort_result.integrator
        comfort_filtered_error = comfort_result.filtered_error
        comfort_offset = comfort_result.offset

        if not heat_enabled and comfort_offset < 0.0:
            comfort_offset = 0.0
            comfort_integrator *= 0.9

    heat_need_factor = clamp(
        (error_c - _COMFORT_DEADBAND_C) / _HEAT_WINDOW_C, 0.0, 1.0
    )
    effective_price_offset = price_offset * (
        1 - heat_need_factor * _brake_reduction_strength(inputs.brake_aggressiveness)
    )
    requested_offset = comfort_offset + effective_price_offset

    if inputs.mode == "Off":
        requested_offset = 0.0
        effective_price_offset = 0.0
        price_offset = 0.0

    price_bias_active = price_offset > _PRICE_BIAS_THRESHOLD_C
    net_braking = (requested_offset > _PRICE_BIAS_THRESHOLD_C) and price_bias_active
    net_heating = requested_offset < -_PRICE_BIAS_THRESHOLD_C

    if inputs.mode == "Off":
        status = "Off"
        reason_code = "OFF"
        effective_mode = "off"
    elif limiting_comfort:
        status = "Braking (limiting comfort)"
        reason_code = "PRICE_LIMITING_COMFORT"
        effective_mode = "limiting_comfort"
    elif net_braking:
        price_brake_reason = price_reason_code
        if price_brake_reason is None and price_bias_active and not in_peak:
            price_brake_reason = "PRICE_BRAKE_DECAY"
        if price_brake_reason == "PRICE_BRAKE_ENTER":
            status = "Braking (entering peak)"
            reason_code = "PRICE_BRAKE_ENTER"
        elif price_brake_reason == "PRICE_BRAKE_HOLD":
            status = "Braking (peak hold)"
            reason_code = "PRICE_BRAKE_HOLD"
        elif price_brake_reason == "PRICE_BRAKE_DECAY":
            status = "Braking (decaying)"
            reason_code = "PRICE_BRAKE_DECAY"
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
        effective_mode = "boost" if price_state == "boost" else "comfort"
    else:
        status = "Neutral"
        reason_code = "NEUTRAL"
        effective_mode = "neutral"

    if inputs.mode == "Off":
        price_state = None

    return DecisionOutput(
        requested_offset=requested_offset,
        reason_code=reason_code,
        status=status,
        effective_mode=effective_mode,
        price_state=price_state,
        comfort_offset=comfort_offset,
        price_offset=price_offset,
        effective_price_offset=effective_price_offset,
        brake_active=brake_active,
        in_peak=in_peak,
        limiting_comfort=limiting_comfort,
        price_reason_code=price_reason_code,
        price_bias_active=price_bias_active,
        comfort_integrator=comfort_integrator,
        comfort_filtered_error=comfort_filtered_error,
        price_offset_smoothed=price_offset_smoothed,
        last_price_state=last_price_state,
        last_price_state_changed=last_price_state_changed,
    )
