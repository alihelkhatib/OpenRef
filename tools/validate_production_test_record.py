#!/usr/bin/env python3
"""Validate OpenRef production-test evidence and fail closed on missing limits."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


SHA256 = re.compile(r"^[0-9a-f]{64}$")
FINGERPRINT = re.compile(r"^[0-9a-f]{16}$")
DISPOSITIONS = {"PASS", "REWORK", "SCRAP", "QUARANTINE"}
OUTCOMES = {"PASS", "FAIL", "SKIP"}
DEVICE_STATES = {
    "BLANK", "FACTORY_TEST", "IDENTITY_INSTALLED", "PRODUCTION_LOCKED",
    "QUARANTINED", "RETIRED",
}
REQUIRED_STEPS = [f"MFG-{index:02d}" for index in range(1, 14)]
LIMITED_STEPS = {"MFG-02", "MFG-03", "MFG-06", "MFG-07", "MFG-08", "MFG-09", "MFG-10", "MFG-11"}
CALIBRATION_STEPS = {"MFG-02", "MFG-03", "MFG-06", "MFG-08", "MFG-09"}
FORBIDDEN_KEYS = {
    "private_key", "session_key", "provisioning_blob", "recovery_secret",
    "credential_blob", "audio_samples", "audio_capture", "captured_audio",
}


def _find_forbidden(value: Any, path: str = "record") -> list[str]:
    found: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = str(key).lower()
            if normalized in FORBIDDEN_KEYS or any(token in normalized for token in FORBIDDEN_KEYS):
                found.append(f"forbidden sensitive field: {path}.{key}")
            found.extend(_find_forbidden(child, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found.extend(_find_forbidden(child, f"{path}[{index}]"))
    return found


def _utc(value: Any) -> bool:
    return isinstance(value, str) and "T" in value and value.endswith("Z")


def validate(record: dict[str, Any]) -> list[str]:
    errors: list[str] = _find_forbidden(record)
    missing: list[str] = []
    for field in (
        "record_version", "unit_serial", "pcb_lot", "fixture_id",
        "station_id", "limit_set_revision", "firmware", "steps",
        "disposition", "provisioning_anomaly", "device_state",
        "identity_fingerprint",
        "attempt_id", "started_utc", "completed_utc", "limit_set_sha256",
        "fixture_calibration",
    ):
        if field not in record:
            missing.append(f"missing {field}")
    errors.extend(missing)
    if missing:
        return errors
    if record["disposition"] not in DISPOSITIONS:
        errors.append("invalid disposition")
    for field in ("unit_serial", "pcb_lot", "fixture_id", "station_id", "limit_set_revision"):
        if not isinstance(record[field], str) or not record[field].strip():
            errors.append(f"{field} must be a nonempty string")
    if record["record_version"] != 3:
        errors.append("record_version must be 3")
    if not str(record["attempt_id"]).strip():
        errors.append("attempt_id must be nonempty")
    if not _utc(record["started_utc"]) or not _utc(record["completed_utc"]):
        errors.append("record timestamps must be UTC ISO-8601 values")
    elif record["completed_utc"] < record["started_utc"]:
        errors.append("completed_utc precedes started_utc")
    if not SHA256.fullmatch(str(record["limit_set_sha256"])):
        errors.append("limit_set_sha256 must be lowercase SHA-256")
    calibration = record["fixture_calibration"]
    if not isinstance(calibration, dict) or not str(calibration.get("fixture_id", "")).strip() or \
       not SHA256.fullmatch(str(calibration.get("certificate_sha256", ""))) or \
       not _utc(calibration.get("calibration_due_utc")):
        errors.append("fixture_calibration requires fixture ID, due UTC, and certificate SHA-256")
    elif calibration["fixture_id"] != record["fixture_id"]:
        errors.append("fixture calibration does not match fixture_id")
    elif _utc(record["completed_utc"]) and calibration["calibration_due_utc"] < record["completed_utc"]:
        errors.append("fixture calibration expired before record completion")
    if record["device_state"] not in DEVICE_STATES:
        errors.append("invalid device_state")
    if not FINGERPRINT.fullmatch(str(record["identity_fingerprint"])):
        errors.append("identity_fingerprint must be 8-byte lowercase hex")
    if not isinstance(record["steps"], list) or not record["steps"]:
        errors.append("steps must be a nonempty list")
        return errors
    if not isinstance(record["firmware"], dict):
        errors.append("firmware must be an object")
        return errors
    for processor in ("radio_sha256", "audio_sha256"):
        digest = str(record["firmware"].get(processor, ""))
        if not SHA256.fullmatch(digest):
            errors.append(f"firmware.{processor} must be lowercase SHA-256")

    failed = False
    seen_ids: set[str] = set()
    actual_step_ids = [str(step.get("test_id", "")) if isinstance(step, dict) else ""
                       for step in record["steps"]]
    if actual_step_ids != REQUIRED_STEPS:
        errors.append("steps must contain MFG-01 through MFG-13 exactly in order")
    previous_completion = record["started_utc"] if _utc(record["started_utc"]) else None
    for index, step in enumerate(record["steps"]):
        prefix = f"steps[{index}]"
        if not isinstance(step, dict):
            errors.append(f"{prefix} must be an object")
            continue
        test_id = str(step.get("test_id", ""))
        if not test_id or test_id in seen_ids:
            errors.append(f"{prefix}.test_id is missing or duplicated")
        seen_ids.add(test_id)
        outcome = step.get("outcome")
        if outcome not in OUTCOMES:
            errors.append(f"{prefix}.outcome is invalid")
        if outcome == "FAIL":
            failed = True
            if not step.get("failure_code"):
                errors.append(f"{prefix}.failure_code required for FAIL")
        if outcome == "SKIP" and not step.get("skip_authorization"):
            errors.append(f"{prefix}.skip_authorization required for SKIP")
        if not _utc(step.get("started_utc")) or not _utc(step.get("completed_utc")):
            errors.append(f"{prefix} requires UTC start and completion timestamps")
        elif step["completed_utc"] < step["started_utc"]:
            errors.append(f"{prefix} completion precedes start")
        else:
            if previous_completion is not None and step["started_utc"] < previous_completion:
                errors.append(f"{prefix} starts before the previous step completed")
            if _utc(record["started_utc"]) and step["started_utc"] < record["started_utc"]:
                errors.append(f"{prefix} starts before the record")
            if _utc(record["completed_utc"]) and step["completed_utc"] > record["completed_utc"]:
                errors.append(f"{prefix} completes after the record")
            previous_completion = step["completed_utc"]
        if test_id in LIMITED_STEPS and step.get("limits_required") is not True:
            errors.append(f"{prefix} must require controlled limits")
        if test_id in CALIBRATION_STEPS:
            instruments = step.get("instruments")
            if not isinstance(instruments, list) or not instruments:
                errors.append(f"{prefix} requires calibrated instrument evidence")
            else:
                for instrument in instruments:
                    if not isinstance(instrument, dict) or not str(instrument.get("instrument_id", "")).strip() or \
                       not _utc(instrument.get("calibration_due_utc")) or \
                       not SHA256.fullmatch(str(instrument.get("certificate_sha256", ""))):
                        errors.append(f"{prefix} has invalid calibrated instrument evidence")
                        break
                    if _utc(step.get("completed_utc")) and instrument["calibration_due_utc"] < step["completed_utc"]:
                        errors.append(f"{prefix} uses an expired instrument calibration")
                        break
        measurements = step.get("measurements", [])
        if not isinstance(measurements, list):
            errors.append(f"{prefix}.measurements must be a list")
            continue
        if step.get("limits_required", False) and not measurements:
            errors.append(f"{prefix} requires at least one bounded measurement")
        for measurement_index, measurement in enumerate(measurements):
            label = f"{prefix}.measurements[{measurement_index}]"
            if not isinstance(measurement, dict):
                errors.append(f"{label} must be an object")
                continue
            if not measurement.get("name") or not measurement.get("unit"):
                errors.append(f"{label} requires name and unit")
            if "value" not in measurement:
                errors.append(f"{label}.value is missing")
            if (
                step.get("limits_required", False)
                and measurement.get("minimum") is None
                and measurement.get("maximum") is None
            ):
                errors.append(f"{label} has no acceptance limit")
            value = measurement.get("value")
            minimum = measurement.get("minimum")
            maximum = measurement.get("maximum")
            numeric = lambda item: isinstance(item, (int, float)) and not isinstance(item, bool)
            if not numeric(value):
                errors.append(f"{label}.value must be numeric")
                continue
            if minimum is not None and not numeric(minimum):
                errors.append(f"{label}.minimum must be numeric or null")
                continue
            if maximum is not None and not numeric(maximum):
                errors.append(f"{label}.maximum must be numeric or null")
                continue
            if minimum is not None and maximum is not None and minimum > maximum:
                errors.append(f"{label} minimum exceeds maximum")
            if minimum is not None and value < minimum:
                errors.append(f"{label}.value is below minimum")
            if maximum is not None and value > maximum:
                errors.append(f"{label}.value is above maximum")

    if not isinstance(record["provisioning_anomaly"], bool):
        errors.append("provisioning_anomaly must be boolean")
    if record["provisioning_anomaly"] and record["disposition"] != "QUARANTINE":
        errors.append("provisioning anomaly requires QUARANTINE")
    if record["provisioning_anomaly"] and record["device_state"] != "QUARANTINED":
        errors.append("provisioning anomaly requires QUARANTINED device_state")
    if failed and record["disposition"] == "PASS":
        errors.append("failed step prohibits PASS disposition")
    if record["disposition"] == "PASS" and any(
        not isinstance(step, dict) or step.get("outcome") != "PASS"
        for step in record["steps"]
    ):
        errors.append("PASS disposition requires every step to pass")
    if record["disposition"] == "PASS" and record["device_state"] != "PRODUCTION_LOCKED":
        errors.append("PASS disposition requires PRODUCTION_LOCKED device_state")
    if record["disposition"] == "QUARANTINE" and record["device_state"] != "QUARANTINED":
        errors.append("QUARANTINE disposition requires QUARANTINED device_state")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a production test record")
    parser.add_argument("record", type=Path)
    args = parser.parse_args()
    errors = validate(json.loads(args.record.read_text(encoding="utf-8")))
    for error in errors:
        print(error)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
