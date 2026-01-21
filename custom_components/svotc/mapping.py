"""Mapping helpers for aggressiveness to offsets."""

from __future__ import annotations

BRAKE_OFFSETS: list[float] = [0, 3, 5, 7, 9, 10]
HEAT_OFFSETS: list[float] = [0, -1, -2, -3, -4, -5]


def _clamp_level(level: int) -> int:
    """Clamp aggressiveness to the supported range."""
    return max(0, min(5, level))


def brake_offset(level: int) -> float:
    """Return the brake offset for a given aggressiveness."""
    return float(BRAKE_OFFSETS[_clamp_level(level)])


def heat_offset(level: int) -> float:
    """Return the heat offset for a given aggressiveness."""
    return float(HEAT_OFFSETS[_clamp_level(level)])


def max_abs_offset() -> float:
    """Return the maximum absolute offset used for ramping."""
    return max(abs(max(BRAKE_OFFSETS)), abs(min(HEAT_OFFSETS)))
