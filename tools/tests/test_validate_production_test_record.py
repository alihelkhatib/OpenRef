import importlib.util
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "validate_production_test_record.py"
SPEC = importlib.util.spec_from_file_location("production_record", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def valid_record() -> dict:
    steps = []
    for index in range(1, 14):
        test_id = f"MFG-{index:02d}"
        limited = test_id in MODULE.LIMITED_STEPS
        step = {
            "test_id": test_id,
            "started_utc": f"2026-08-14T12:{index:02d}:00Z",
            "completed_utc": f"2026-08-14T12:{index:02d}:30Z",
            "outcome": "PASS",
            "limits_required": limited,
            "measurements": ([{
                "name": "controlled measurement", "unit": "unit",
                "value": 10, "minimum": 5, "maximum": 15,
            }] if limited else []),
        }
        if test_id in MODULE.CALIBRATION_STEPS:
            step["instruments"] = [{
                "instrument_id": "INST-1",
                "calibration_due_utc": "2027-01-01T00:00:00Z",
                "certificate_sha256": "c" * 64,
            }]
        steps.append(step)
    return {
        "record_version": 3,
        "attempt_id": "OR-000001-A1",
        "started_utc": "2026-08-14T12:00:00Z",
        "completed_utc": "2026-08-14T13:00:00Z",
        "unit_serial": "OR-000001",
        "pcb_lot": "P1-A",
        "fixture_id": "FIX-1",
        "station_id": "STATION-1",
        "limit_set_revision": "P1-0.1",
        "limit_set_sha256": "d" * 64,
        "fixture_calibration": {
            "fixture_id": "FIX-1",
            "calibration_due_utc": "2027-01-01T00:00:00Z",
            "certificate_sha256": "e" * 64,
        },
        "firmware": {"radio_sha256": "a" * 64, "audio_sha256": "b" * 64},
        "provisioning_anomaly": False,
        "device_state": "PRODUCTION_LOCKED",
        "identity_fingerprint": "0123456789abcdef",
        "disposition": "PASS",
        "steps": steps,
    }


def test_valid_record_passes() -> None:
    assert MODULE.validate(valid_record()) == []


def test_empty_limit_cannot_default_to_pass() -> None:
    record = valid_record()
    record["steps"][1]["measurements"][0]["minimum"] = None
    record["steps"][1]["measurements"][0]["maximum"] = None
    assert any("no acceptance limit" in error for error in MODULE.validate(record))


def test_failure_and_provisioning_anomaly_cannot_pass() -> None:
    record = valid_record()
    record["steps"][0]["outcome"] = "FAIL"
    record["provisioning_anomaly"] = True
    errors = MODULE.validate(record)
    assert any("failure_code" in error for error in errors)
    assert any("QUARANTINE" in error for error in errors)
    assert any("prohibits PASS" in error for error in errors)


def test_malformed_measurement_reports_error_instead_of_throwing() -> None:
    record = valid_record()
    record["steps"][1]["measurements"][0]["value"] = "ten"
    assert any("must be numeric" in error for error in MODULE.validate(record))


def test_pass_requires_locked_identity_and_valid_fingerprint() -> None:
    record = valid_record()
    record["device_state"] = "IDENTITY_INSTALLED"
    record["identity_fingerprint"] = "secret-key-material"
    errors = MODULE.validate(record)
    assert any("PRODUCTION_LOCKED" in error for error in errors)
    assert any("identity_fingerprint" in error for error in errors)


def test_provisioning_anomaly_requires_quarantined_state() -> None:
    record = valid_record()
    record["provisioning_anomaly"] = True
    record["disposition"] = "QUARANTINE"
    errors = MODULE.validate(record)
    assert any("QUARANTINED device_state" in error for error in errors)


def test_missing_or_reordered_manufacturing_steps_cannot_pass() -> None:
    record = valid_record()
    record["steps"].pop(5)
    assert any("MFG-01 through MFG-13" in error for error in MODULE.validate(record))
    record = valid_record()
    record["steps"][0], record["steps"][1] = record["steps"][1], record["steps"][0]
    assert any("exactly in order" in error for error in MODULE.validate(record))


def test_calibration_timestamps_and_sensitive_fields_are_enforced() -> None:
    record = valid_record()
    record["steps"][1]["instruments"] = []
    record["private_key"] = "must never be recorded"
    record["completed_utc"] = "2026-08-14T11:00:00Z"
    errors = MODULE.validate(record)
    assert any("calibrated instrument" in error for error in errors)
    assert any("forbidden sensitive field" in error for error in errors)
    assert any("precedes" in error for error in errors)


def test_expired_calibration_and_overlapping_steps_are_rejected() -> None:
    record = valid_record()
    record["fixture_calibration"]["calibration_due_utc"] = "2026-08-14T12:30:00Z"
    record["steps"][1]["instruments"][0]["calibration_due_utc"] = "2026-08-14T12:01:00Z"
    record["steps"][2]["started_utc"] = "2026-08-14T12:02:00Z"
    record["steps"][1]["completed_utc"] = "2026-08-14T12:02:30Z"
    errors = MODULE.validate(record)
    assert any("fixture calibration expired" in error for error in errors)
    assert any("expired instrument" in error for error in errors)
    assert any("previous step" in error for error in errors)
