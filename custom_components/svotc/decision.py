"""Decision logic for SVOTC."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from .mapping import brake_offset, heat_offset

_DWELL_TIME = timedelta(minutes=30)

_STATUS_BY_REASON = {
    "SMART_FULL": "Smart (price + forecast)",
    "SMART_PRICE_ONLY": "Smart (price only)",
    "MISSING_FORECAST": "Missing forecast",
    "MISSING_PRICE": "Missing price",
    "MISSING_BOTH": "Missing price and forecast",
    "MISSING_INDOOR": "Missing indoor temperature",
    "OFF": "Off",
    "FORECAST_HEAT_NEED": "Boosting (cold forecast ahead)",
    "PRICE_BRAKE": "Braking (expensive price)",
    "PRICE_ELEVATED": "Braking (price elevated)",
    "PRICE_BOOST": "Boosting (cheap price)",
    "SAFETY_ANCHOR": "Safety anchor",
    "NEUTRAL": "Neutral",
    "TEMP_GLITCH_HOLD": "Holding (sensor glitch)",
}


@dataclass(frozen=True)
class DecisionInput:
    """Inputs required for the decision logic."""

    mode: str
    indoor_temp: float | None
    outdoor_temp: float | None
    dynamic_target: float
    brake_aggressiveness: int
    heat_aggressiveness: int
    price_class: str | None
    current_price: float | None
    price_p30: float | None
    price_p70: float | None
    forecast_min_next_6h: float | None  # NOTE: may contain 12h min if coordinator uses 12h window
    price_available: bool
    forecast_available: bool
    now: datetime
    last_price_state: str | None
    last_price_state_changed: datetime | None


@dataclass(frozen=True)
class DecisionOutput:
    """Decision output values."""

    target_offset: float
    reason_code: str
    status: str
    price_state: str | None


def _status_for_reason(reason: str) -> str:
    """Return a status string for a reason code."""
    return _STATUS_BY_REASON.get(reason, reason)


def _availability_code(price_available: bool, forecast_available: bool) -> str:
    """Return the availability code for price/forecast inputs."""
    if price_available and forecast_available:
        return "SMART_FULL"
    if price_available:
        return "SMART_PRICE_ONLY"
    if forecast_available:
        return "MISSING_PRICE"
    return "MISSING_BOTH"


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


def decide(inputs: DecisionInput) -> DecisionOutput:
    """Return the decision for the current update cycle."""
    if inputs.mode == "Off":
        return DecisionOutput(0.0, "OFF", _status_for_reason("OFF"), None)

    if inputs.indoor_temp is None:
        return DecisionOutput(
            0.0, "MISSING_INDOOR", _status_for_reason("MISSING_INDOOR"), None
        )

    availability = _availability_code(inputs.price_available, inputs.forecast_available)

    # Only anchor for safety when we are missing critical decision inputs.
    # Add a small deadband to avoid anchoring on tiny differences.
    safety_margin = 0.3  # °C
    safety_needed = inputs.indoor_temp < (inputs.dynamic_target - safety_margin)

    if availability in ("MISSING_PRICE", "MISSING_BOTH"):
        if safety_needed:
            return DecisionOutput(
                heat_offset(inputs.heat_aggressiveness),
                "SAFETY_ANCHOR",
                _status_for_reason("SAFETY_ANCHOR"),
                None,
            )
        return DecisionOutput(
            0.0,
            availability,
            _status_for_reason(availability),
            None,
        )

    price_state: str | None = None
    target_offset = 0.0
    reason_code = availability
    status = _status_for_reason(availability)

    if (
        inputs.price_available
        and inputs.current_price is not None
        and inputs.price_p30 is not None
        and inputs.price_p70 is not None
        and inputs.price_p70 > inputs.price_p30
    ):
        max_brake = brake_offset(inputs.brake_aggressiveness)
        if inputs.current_price <= inputs.price_p30:
            target_offset = 0.0
            reason_code = "NEUTRAL"
            price_state = "neutral"
        elif inputs.current_price >= inputs.price_p70:
            target_offset = max_brake
            reason_code = "PRICE_BRAKE"
            price_state = "brake"
        else:
            ratio = (inputs.current_price - inputs.price_p30) / (
                inputs.price_p70 - inputs.price_p30
            )
            ratio = max(0.0, min(1.0, ratio))
            target_offset = ratio * max_brake
            reason_code = "PRICE_ELEVATED"
            price_state = "brake"
    else:
        if inputs.price_class == "expensive":
            target_offset = brake_offset(inputs.brake_aggressiveness)
            reason_code = "PRICE_BRAKE"
            price_state = "brake"
        elif inputs.price_class == "cheap":
            target_offset = heat_offset(inputs.heat_aggressiveness)
            reason_code = "PRICE_BOOST"
            price_state = "boost"
        elif inputs.price_class == "neutral":
            target_offset = 0.0
            reason_code = "NEUTRAL"
            price_state = "neutral"

    if (
        inputs.forecast_available
        and inputs.price_class == "neutral"
        and inputs.outdoor_temp is not None
        and inputs.forecast_min_next_6h is not None
        and inputs.indoor_temp < inputs.dynamic_target + 0.2
        and inputs.forecast_min_next_6h < inputs.outdoor_temp - 2.0
    ):
        return DecisionOutput(
            heat_offset(inputs.heat_aggressiveness),
            "FORECAST_HEAT_NEED",
            _status_for_reason("FORECAST_HEAT_NEED"),
            None,
        )

    if price_state is not None:
        applied_state = _apply_price_dwell(
            price_state,
            inputs.last_price_state,
            inputs.last_price_state_changed,
            inputs.now,
        )
        if applied_state != price_state:
            price_state = applied_state
            if applied_state == "brake":
                target_offset = brake_offset(inputs.brake_aggressiveness)
                reason_code = "PRICE_BRAKE"
            elif applied_state == "boost":
                target_offset = heat_offset(inputs.heat_aggressiveness)
                reason_code = "PRICE_BOOST"
            else:
                target_offset = 0.0
                reason_code = "NEUTRAL"

    status = _status_for_reason(reason_code)
    return DecisionOutput(target_offset, reason_code, status, price_state)
