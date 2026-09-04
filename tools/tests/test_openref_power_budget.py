import importlib.util
from pathlib import Path

import pytest


SCRIPT = Path(__file__).parents[1] / "openref_power_budget.py"
SPEC = importlib.util.spec_from_file_location("openref_power_budget", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_power_budget_math_and_reserves() -> None:
    result = MODULE.evaluate({
        "name": "test",
        "status": "assumed",
        "target_endurance_h": 8,
        "battery": {
            "nominal_voltage_v": 4,
            "capacity_mah": 1000,
            "usable_capacity_factors": {"aging": 0.8, "warning": 0.5},
        },
        "loads": [{
            "name": "load",
            "evidence": "assumed",
            "voltage_v": 2,
            "current_ma": 100,
            "duty_cycle": 0.5,
            "conversion_efficiency": 0.5,
        }],
    })
    assert result["total_average_mw"] == 200
    assert result["usable_battery_wh"] == 1.6
    assert result["estimated_endurance_h"] == 8
    assert result["required_nominal_capacity_mah"] == 1000
    assert result["maximum_average_mw_at_target"] == 200
    assert result["load_headroom_factor"] == 1
    assert not result["release_ready"]
    assert len(result["unmeasured_inputs"]) == 4


def test_power_budget_rejects_invalid_factor() -> None:
    with pytest.raises(ValueError):
        MODULE.evaluate({
            "name": "bad",
            "status": "assumed",
            "target_endurance_h": 8,
            "battery": {
                "nominal_voltage_v": 3.7,
                "capacity_mah": 1000,
                "usable_capacity_factors": {"bad": 0},
            },
            "loads": [],
        })


def test_power_budget_marks_fully_measured_input_release_ready() -> None:
    result = MODULE.evaluate({
        "name": "measured",
        "status": "measured",
        "target_endurance_h": 1,
        "battery": {
            "nominal_voltage_v": 4,
            "capacity_mah": 100,
            "capacity_evidence_class": "measured",
            "usable_capacity_factors": {"aging": 0.8},
            "factor_evidence_class": {"aging": "measured"},
        },
        "loads": [{
            "name": "measured load",
            "evidence": "trace.csv",
            "evidence_class": "measured",
            "power_mw": 100,
        }],
    })
    assert result["release_ready"]
    assert result["unmeasured_inputs"] == []


def test_power_budget_rejects_zero_total_load() -> None:
    with pytest.raises(ValueError):
        MODULE.evaluate({
            "name": "zero",
            "status": "assumed",
            "target_endurance_h": 1,
            "battery": {
                "nominal_voltage_v": 4,
                "capacity_mah": 100,
                "usable_capacity_factors": {"aging": 1},
            },
            "loads": [{
                "name": "off", "evidence": "assumed", "power_mw": 0,
            }],
        })


def test_power_budget_loader_rejects_duplicate_evidence_keys(
    tmp_path: Path,
) -> None:
    config = tmp_path / "duplicate.json"
    config.write_text(
        '{"name":"x","name":"y","status":"assumed"}',
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="duplicate JSON key: name"):
        MODULE.load_config(config)
