"""Tests for SVOTC decision logic."""

from __future__ import annotations

import sys
from dataclasses import replace
import importlib.util
from datetime import datetime, timedelta, timezone
from pathlib import Path
import types

ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = ROOT / "custom_components"
SVOTC_ROOT = PACKAGE_ROOT / "svotc"

custom_components_pkg = types.ModuleType("custom_components")
custom_components_pkg.__path__ = [str(PACKAGE_ROOT)]
sys.modules["custom_components"] = custom_components_pkg

svotc_pkg = types.ModuleType("custom_components.svotc")
svotc_pkg.__path__ = [str(SVOTC_ROOT)]
sys.modules["custom_components.svotc"] = svotc_pkg

DECISION_PATH = SVOTC_ROOT / "decision.py"
SPEC = importlib.util.spec_from_file_location(
    "custom_components.svotc.decision", DECISION_PATH
)
assert SPEC and SPEC.loader
DECISION = importlib.util.module_from_spec(SPEC)
sys.modules["custom_components.svotc.decision"] = DECISION
SPEC.loader.exec_module(DECISION)

decide = DECISION.decide
DecisionInput = DECISION.DecisionInput
DecisionState = DECISION.DecisionState


def _base_input(now: datetime) -> DecisionInput:
    return DecisionInput(
        mode="Home",
        indoor_temp=20.0,
        outdoor_temp=5.0,
        dynamic_target=20.0,
        brake_aggressiveness=2,
        heat_aggressiveness=2,
        current_price=100.0,
        price_class="expensive",
        p70=70.0,
        p80=80.0,
        price_available=True,
        forecast_available=True,
        now=now,
        dt_seconds=60.0,
        require_indoor=True,
        require_outdoor=True,
        require_price=True,
        require_forecast=True,
    )


def _base_state(now: datetime) -> DecisionState:
    return DecisionState(
        comfort_integrator=0.0,
        comfort_filtered_error=0.0,
        price_offset_smoothed=None,
        brake_active=False,
        last_price_state="neutral",
        last_price_state_changed=now - timedelta(minutes=45),
    )


def test_decision_off_mode() -> None:
    now = datetime(2025, 1, 1, tzinfo=timezone.utc)
    inputs = replace(_base_input(now), indoor_temp=21.0)
    state = _base_state(now)
    output = decide(replace(inputs, mode="Off"), state)

    assert output.requested_offset == 0.0
    assert output.reason_code == "OFF"
    assert output.status == "Off"
    assert output.effective_mode == "off"
    assert output.price_state is None


def test_decision_missing_indoor() -> None:
    now = datetime(2025, 1, 1, tzinfo=timezone.utc)
    inputs = _base_input(now)
    state = _base_state(now)
    output = decide(
        replace(inputs, indoor_temp=None),
        state,
    )

    assert output.requested_offset == 0.0
    assert output.reason_code == "MISSING_INDOOR"
    assert output.status == "Missing Indoor"
    assert output.effective_mode == "neutral"


def test_expensive_short_spike_is_ignored() -> None:
    now = datetime(2025, 1, 1, tzinfo=timezone.utc)
    inputs = _base_input(now)
    state = DecisionState(
        comfort_integrator=0.0,
        comfort_filtered_error=0.0,
        price_offset_smoothed=None,
        brake_active=False,
        last_price_state="neutral",
        last_price_state_changed=now - timedelta(minutes=10),
    )

    output = decide(inputs, state)

    assert output.requested_offset == 0.0
    assert output.reason_code == "NEUTRAL"
    assert output.price_state == "neutral"


def test_expensive_over_dwell_triggers_brake() -> None:
    now = datetime(2025, 1, 1, tzinfo=timezone.utc)
    inputs = replace(_base_input(now), indoor_temp=21.0)
    state = DecisionState(
        comfort_integrator=0.0,
        comfort_filtered_error=0.0,
        price_offset_smoothed=None,
        brake_active=False,
        last_price_state="neutral",
        last_price_state_changed=now - timedelta(minutes=31),
    )

    output = decide(inputs, state)

    assert output.requested_offset > 0.0
    assert output.reason_code == "PRICE_BRAKE_ENTER"
    assert output.price_state == "brake"
