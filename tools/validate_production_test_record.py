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


def validate(record: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for field in (
        "record_version", "unit_serial", "pcb_lot", "fixture_id",
        "station_id", "limit_set_revision", "firmware", "steps",
        "disposition", "provisioning_anomaly", "device_state",
        "identity_fingerprint",
    ):
        if field not in record:
            errors.append(f"missing {field}")
    if errors:
        return errors
    if record["disposition"] not in DISPOSITIONS:
        errors.append("invalid disposition")
    if record["record_version"] != 2:
        errors.append("record_version must be 2")
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
