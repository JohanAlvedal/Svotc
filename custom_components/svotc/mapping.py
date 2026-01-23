"""Mapping helpers for aggressiveness to offsets."""

from __future__ import annotations

def _clamp_level(level: int) -> int:
    """Clamp aggressiveness to the supported range."""
    return max(0, min(5, level))


def map_brake_offset(level: int) -> float:
    """Return the mapped brake offset for a given aggressiveness."""
    clamped = _clamp_level(level)
    if clamped == 0:
        return 0.0
    if clamped == 1:
        return 3.0
    return 3.0 + (clamped - 1) * 1.75


def map_heat_offset(level: int) -> float:
    """Return the mapped heat offset for a given aggressiveness."""
    clamped = _clamp_level(level)
    if clamped == 0:
        return 0.0
    return -1.0 * clamped


def brake_offset(level: int) -> float:
    """Return the brake offset for a given aggressiveness."""
    return map_brake_offset(level)


def heat_offset(level: int) -> float:
    """Return the heat offset for a given aggressiveness."""
    return map_heat_offset(level)


def max_abs_offset() -> float:
    """Return the maximum absolute offset used for ramping."""
    return max(abs(map_brake_offset(5)), abs(map_heat_offset(5)))
