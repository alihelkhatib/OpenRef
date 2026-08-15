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


def test_power_budget_marks_fully_measured_input_release_ready(tmp_path: Path) -> None:
    import hashlib

    capture = tmp_path / "capture.csv"
    capture.write_bytes(b"measured current")
    evidence = {
        "artifact_file": "capture.csv",
        "sha256": hashlib.sha256(b"measured current").hexdigest(),
        "method": "integrated current capture",
        "instrument": "calibrated analyzer",
        "captured_utc": "2026-08-14T12:00:00Z",
    }
    config = {
        "name": "measured",
        "status": "measured",
        "target_endurance_h": 1,
        "battery": {
            "nominal_voltage_v": 4,
            "capacity_mah": 100,
            "capacity_evidence_class": "measured",
            "capacity_evidence": evidence,
            "usable_capacity_factors": {"aging": 0.8},
            "factor_evidence_class": {"aging": "measured"},
            "factor_evidence": {"aging": evidence},
        },
        "loads": [{
            "name": "measured load",
            "evidence": evidence,
            "evidence_class": "measured",
            "power_mw": 100,
        }],
    }
    assert not MODULE.evaluate(config)["release_ready"]
    result = MODULE.evaluate(config, tmp_path)
    assert result["release_ready"]
    assert result["measurement_artifacts_verified"]
    assert result["unmeasured_inputs"] == []


def test_measured_label_without_traceable_evidence_is_not_release_ready() -> None:
    result = MODULE.evaluate({
        "name": "false measured claim",
        "status": "measured",
        "target_endurance_h": 1,
        "battery": {
            "nominal_voltage_v": 4,
            "capacity_mah": 100,
            "capacity_evidence_class": "measured",
            "capacity_evidence": "capacity.csv",
            "usable_capacity_factors": {"aging": 0.8},
            "factor_evidence_class": {"aging": "measured"},
            "factor_evidence": {"aging": {"artifact_file": "../escape.csv"}},
        },
        "loads": [{
            "name": "load", "evidence": "trace.csv",
            "evidence_class": "measured", "power_mw": 100,
        }],
    })
    assert not result["release_ready"]
    assert len([item for item in result["unmeasured_inputs"] if "traceable_evidence" in item]) == 3


def test_measured_artifact_tampering_blocks_release(tmp_path: Path) -> None:
    import hashlib

    capture = tmp_path / "capture.csv"
    capture.write_bytes(b"original")
    evidence = {
        "artifact_file": "capture.csv",
        "sha256": hashlib.sha256(b"original").hexdigest(),
        "method": "integration", "instrument": "analyzer",
        "captured_utc": "2026-08-14T12:00:00Z",
    }
    config = {
        "name": "measured", "status": "measured", "target_endurance_h": 1,
        "battery": {"nominal_voltage_v": 4, "capacity_mah": 100,
                    "capacity_evidence_class": "measured", "capacity_evidence": evidence,
                    "usable_capacity_factors": {"aging": 1},
                    "factor_evidence_class": {"aging": "measured"},
                    "factor_evidence": {"aging": evidence}},
        "loads": [{"name": "load", "evidence": evidence,
                   "evidence_class": "measured", "power_mw": 100}],
    }
    assert MODULE.evaluate(config, tmp_path)["release_ready"]
    capture.write_bytes(b"tampered")
    result = MODULE.evaluate(config, tmp_path)
    assert not result["release_ready"]
    assert any("hash mismatch" in error for error in result["artifact_errors"])


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


def test_power_budget_loader_rejects_duplicate_keys(tmp_path: Path) -> None:
    path = tmp_path / "duplicate.json"
    path.write_text('{"name": "one", "name": "two"}', encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate JSON key: name"):
        MODULE.load_config(path)
