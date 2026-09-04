import importlib.util
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "validate_production_test_record.py"
SPEC = importlib.util.spec_from_file_location("production_record", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def valid_record() -> dict:
    return {
        "record_version": 2,
        "unit_serial": "OR-000001",
        "pcb_lot": "P1-A",
        "fixture_id": "FIX-1",
        "station_id": "STATION-1",
        "limit_set_revision": "P1-0.1",
        "firmware": {"radio_sha256": "a" * 64, "audio_sha256": "b" * 64},
        "provisioning_anomaly": False,
        "device_state": "PRODUCTION_LOCKED",
        "identity_fingerprint": "0123456789abcdef",
        "disposition": "PASS",
        "steps": [{
            "test_id": "PWR-01",
            "outcome": "PASS",
            "limits_required": True,
            "measurements": [{
                "name": "radio idle", "unit": "mA", "value": 10,
                "minimum": 5, "maximum": 15,
            }],
        }],
    }


def test_valid_record_passes() -> None:
    assert MODULE.validate(valid_record()) == []


def test_empty_limit_cannot_default_to_pass() -> None:
    record = valid_record()
    record["steps"][0]["measurements"][0]["minimum"] = None
    record["steps"][0]["measurements"][0]["maximum"] = None
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
    record["steps"][0]["measurements"][0]["value"] = "ten"
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
