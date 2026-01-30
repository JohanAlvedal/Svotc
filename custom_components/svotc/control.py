"""Control helpers for SVOTC."""

from __future__ import annotations

from dataclasses import dataclass
import math


@dataclass(slots=True)
class ComfortPIResult:
    """Result of a comfort PI update."""

    offset: float
    integrator: float
    filtered_error: float


@dataclass(slots=True)
class BrakeDecision:
    """Decision details for price braking."""

    target_offset: float
    brake_active: bool
    in_peak: bool
    reason_code: str | None
    limited_by_comfort: bool


def clamp(value: float, min_value: float, max_value: float) -> float:
    """Clamp a value between min and max."""
    return max(min_value, min(max_value, value))


def low_pass_filter(
    value: float,
    last_value: float | None,
    dt_seconds: float,
    time_constant_seconds: float,
) -> float:
    """Apply a first-order low-pass filter to a value."""
    if last_value is None:
        return value
    if dt_seconds <= 0 or time_constant_seconds <= 0:
        return value
    alpha = 1 - math.exp(-dt_seconds / time_constant_seconds)
    return last_value + alpha * (value - last_value)


def compute_price_offset(
    current_price: float | None,
    p30: float | None,
    p70: float | None,
    max_brake_offset: float,
) -> tuple[float, float | None]:
    """Compute a scaled price brake offset and ratio."""
    if (
        current_price is None
        or p30 is None
        or p70 is None
        or max_brake_offset <= 0
        or p70 <= p30
    ):
        return 0.0, None
    if current_price <= p30:
        return 0.0, 0.0
    if current_price >= p70:
        return max_brake_offset, 1.0
    ratio = (current_price - p30) / (p70 - p30)
    ratio = clamp(ratio, 0.0, 1.0)
    return ratio * max_brake_offset, ratio


def compute_brake_target(
    current_price: float | None,
    p70: float | None,
    p80: float | None,
    max_brake_offset: float,
    brake_active: bool,
    last_offset: float | None,
    comfort_guard_active: bool,
) -> BrakeDecision:
    """Compute a stateful brake target using P80 enter and P70 exit thresholds."""
    if (
        current_price is None
        or p70 is None
        or p80 is None
        or max_brake_offset <= 0
        or p80 <= p70
    ):
        return BrakeDecision(
            target_offset=0.0,
            brake_active=False,
            in_peak=False,
            reason_code=None,
            limited_by_comfort=False,
        )

    in_peak = current_price > p80
    if in_peak:
        next_brake_active = True
    elif current_price < p70:
        next_brake_active = False
    else:
        next_brake_active = brake_active

    target_offset = max_brake_offset if in_peak else 0.0
    limited_by_comfort = False
    if comfort_guard_active and target_offset > 0.0:
        cap = last_offset if last_offset is not None else 0.0
        if target_offset > cap:
            target_offset = cap
            limited_by_comfort = True

    if in_peak:
        reason_code = "PRICE_BRAKE_ENTER" if not brake_active else "PRICE_BRAKE_HOLD"
    elif brake_active:
        reason_code = "PRICE_BRAKE_DECAY"
    else:
        reason_code = None

    return BrakeDecision(
        target_offset=target_offset,
        brake_active=next_brake_active,
        in_peak=in_peak,
        reason_code=reason_code,
        limited_by_comfort=limited_by_comfort,
    )


def smooth_asymmetric(
    target: float,
    last_value: float | None,
    dt_seconds: float,
    decay_time_constant_seconds: float,
) -> float:
    """Smooth a target asymmetrically (fast rise, slow fall)."""
    if last_value is None:
        return target
    if target >= last_value:
        return target
    if dt_seconds <= 0 or decay_time_constant_seconds <= 0:
        return target
    alpha = 1 - math.exp(-dt_seconds / decay_time_constant_seconds)
    return last_value + alpha * (target - last_value)


def update_comfort_pi(
    error_c: float,
    integrator: float,
    filtered_error: float | None,
    dt_seconds: float,
    kp: float,
    ki: float,
    i_min: float,
    i_max: float,
    deadband_c: float,
    max_cool_c: float,
    max_heat_c: float,
    integrate: bool,
    filter_time_constant_seconds: float,
) -> ComfortPIResult:
    """Update comfort PI and return offset + state."""
    if abs(error_c) < deadband_c:
        error_c = 0.0
    filtered = low_pass_filter(
        error_c, filtered_error, dt_seconds, filter_time_constant_seconds
    )
    if integrate and error_c != 0.0 and dt_seconds > 0:
        integrator = clamp(integrator + ki * error_c * dt_seconds, i_min, i_max)
    offset = kp * filtered + integrator
    offset = clamp(offset, -max_cool_c, max_heat_c)
    return ComfortPIResult(offset=offset, integrator=integrator, filtered_error=filtered)
