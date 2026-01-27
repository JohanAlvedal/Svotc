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
