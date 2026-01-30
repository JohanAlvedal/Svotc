"""Tests for SVOTC control helpers."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


CONTROL_PATH = (
    Path(__file__).resolve().parents[1] / "custom_components" / "svotc" / "control.py"
)
SPEC = importlib.util.spec_from_file_location("svotc_control", CONTROL_PATH)
assert SPEC and SPEC.loader
CONTROL = importlib.util.module_from_spec(SPEC)
sys.modules["svotc_control"] = CONTROL
SPEC.loader.exec_module(CONTROL)

compute_price_offset = CONTROL.compute_price_offset
compute_brake_target = CONTROL.compute_brake_target
smooth_asymmetric = CONTROL.smooth_asymmetric
update_comfort_pi = CONTROL.update_comfort_pi


def test_compute_price_offset_scales_between_percentiles() -> None:
    offset, ratio = compute_price_offset(15.0, 10.0, 20.0, 4.0)
    assert ratio == 0.5
    assert offset == 2.0


def test_compute_price_offset_bounds() -> None:
    assert compute_price_offset(5.0, 10.0, 20.0, 4.0) == (0.0, 0.0)
    assert compute_price_offset(25.0, 10.0, 20.0, 4.0) == (4.0, 1.0)
    assert compute_price_offset(None, 10.0, 20.0, 4.0) == (0.0, None)
    assert compute_price_offset(15.0, 20.0, 10.0, 4.0) == (0.0, None)


def test_smooth_asymmetric_rises_immediately_and_decays() -> None:
    assert smooth_asymmetric(3.0, 1.0, 60.0, 300.0) == 3.0
    decayed = smooth_asymmetric(1.0, 3.0, 60.0, 300.0)
    assert 1.0 < decayed < 3.0


def test_update_comfort_pi_integrator_and_clamp() -> None:
    result = update_comfort_pi(
        error_c=1.0,
        integrator=0.0,
        filtered_error=None,
        dt_seconds=10.0,
        kp=-1.0,
        ki=-0.5,
        i_min=-2.0,
        i_max=2.0,
        deadband_c=0.1,
        max_cool_c=3.0,
        max_heat_c=3.0,
        integrate=True,
        filter_time_constant_seconds=0.0,
    )
    assert result.integrator == -2.0
    assert result.offset == -3.0


def test_brake_hysteresis_and_decay_between_peaks() -> None:
    p70 = 70.0
    p80 = 80.0
    max_brake = 4.0
    brake_active = False
    last_offset: float | None = None
    offsets: list[float] = []
    prices = [60.0, 90.0, 75.0, 70.0, 60.0, 90.0]

    for price in prices:
        decision = compute_brake_target(
            current_price=price,
            p70=p70,
            p80=p80,
            max_brake_offset=max_brake,
            brake_active=brake_active,
            last_offset=last_offset,
            comfort_guard_active=False,
        )
        brake_active = decision.brake_active
        last_offset = smooth_asymmetric(decision.target_offset, last_offset, 60.0, 900.0)
        offsets.append(last_offset)

    assert offsets[1] >= offsets[0]
    assert offsets[2] < offsets[1]
    assert offsets[3] < offsets[2]
    assert offsets[4] < offsets[3]
    assert offsets[5] > offsets[4]


def test_brake_does_not_stick_at_p70() -> None:
    decision = compute_brake_target(
        current_price=70.0,
        p70=70.0,
        p80=80.0,
        max_brake_offset=4.0,
        brake_active=True,
        last_offset=3.0,
        comfort_guard_active=False,
    )
    assert decision.target_offset == 0.0
    decayed = smooth_asymmetric(decision.target_offset, 3.0, 60.0, 900.0)
    assert decayed < 3.0


def test_comfort_guard_limits_brake_ramp() -> None:
    guarded = compute_brake_target(
        current_price=90.0,
        p70=70.0,
        p80=80.0,
        max_brake_offset=4.0,
        brake_active=False,
        last_offset=1.0,
        comfort_guard_active=True,
    )
    assert guarded.target_offset == 1.0
    assert guarded.limited_by_comfort is True
