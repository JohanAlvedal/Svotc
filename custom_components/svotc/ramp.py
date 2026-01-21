"""Offset ramping helpers."""

from __future__ import annotations

import math


def max_delta_per_update(
    max_offset: float, update_interval_s: int = 60, ramp_minutes: int = 20
) -> float:
    """Return the maximum offset delta per update."""
    steps = max(1, int((ramp_minutes * 60) / update_interval_s))
    return max_offset / steps


def ramp_offset(current: float, target: float, max_delta: float) -> float:
    """Limit offset changes to the configured ramp rate."""
    delta = target - current
    if abs(delta) <= max_delta:
        return target
    return current + math.copysign(max_delta, delta)
