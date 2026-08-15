#!/usr/bin/env python3
"""Fail-closed validator for complete OpenRef product release evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


SHA256 = re.compile(r"^[0-9a-f]{64}$")
STATUSES = {"BLOCKED", "FAIL", "PASS"}
GATES = {
    "NETWORK_RADIO", "AUDIO", "POWER_CHARGING", "FIRMWARE_SECURITY_SERVICE",
    "MECHANICAL_ENVIRONMENTAL", "HUMAN_FACTORS_STATUS", "MANUFACTURING_IDENTITY",
    "REGULATORY_RF", "RELEASE_DOCUMENTATION", "INTEGRATED_PRODUCT",
}
ALL_TESTS = {f"AV-{index:03d}" for index in range(1, 41)}


def _utc(value) -> bool:
    return isinstance(value, str) and "T" in value and value.endswith("Z")


def validate_manifest(data: dict) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    blockers: list[str] = []
    if data.get("schema") != "openref-product-release-v1" or data.get("product") != "OpenRef":
        errors.append("invalid product release schema or product")
    gates_list = data.get("gates")
    if not isinstance(gates_list, list):
        return errors + ["gates must be a list"], blockers
    gates = {gate.get("id"): gate for gate in gates_list if isinstance(gate, dict)}
    if len(gates) != len(gates_list) or set(gates) != GATES:
        errors.append("gates must exactly match the ten controlled release domains")
    declared_tests: set[str] = set()
    passed_tests: set[str] = set()
    for gate_id, gate in gates.items():
        status = gate.get("status")
        if status not in STATUSES:
            errors.append(f"{gate_id} has invalid status")
            continue
        required = gate.get("required_tests")
        if not isinstance(required, list) or not required or len(required) != len(set(required)) or \
           any(test not in ALL_TESTS for test in required):
            errors.append(f"{gate_id} has invalid required_tests")
            required = []
        declared_tests.update(required)
        evidence = gate.get("evidence")
        if not isinstance(evidence, list):
            errors.append(f"{gate_id}.evidence must be a list")
            evidence = []
        evidence_tests: set[str] = set()
        for index, item in enumerate(evidence):
            label = f"{gate_id}.evidence[{index}]"
            if not isinstance(item, dict):
                errors.append(f"{label} must be an object")
                continue
            path = Path(str(item.get("artifact_file", "")))
            if not str(path) or path.is_absolute() or ".." in path.parts:
                errors.append(f"{label} requires a safe relative artifact_file")
            if not SHA256.fullmatch(str(item.get("sha256", ""))):
                errors.append(f"{label} requires lowercase SHA-256")
            if not _utc(item.get("executed_utc")):
                errors.append(f"{label} requires executed_utc")
            if item.get("result") != "PASS":
                errors.append(f"{label}.result must be PASS")
            tests = item.get("test_ids")
            if not isinstance(tests, list) or not tests or any(test not in required for test in tests):
                errors.append(f"{label}.test_ids must be a nonempty subset of the gate tests")
            else:
                evidence_tests.update(tests)
        if status == "PASS":
            missing = set(required) - evidence_tests
            if missing:
                errors.append(f"{gate_id} PASS lacks evidence for: {', '.join(sorted(missing))}")
            passed_tests.update(evidence_tests)
            if gate.get("blocker") not in (None, ""):
                errors.append(f"{gate_id} PASS must not retain a blocker")
        else:
            if not isinstance(gate.get("blocker"), str) or not gate["blocker"].strip():
                errors.append(f"{gate_id} {status} requires a blocker")
            blockers.append(gate_id)
    if declared_tests != ALL_TESTS:
        errors.append("release domains must collectively declare AV-001 through AV-040")

    top_status = data.get("status")
    if top_status not in STATUSES:
        errors.append("invalid top-level release status")
    all_gates_pass = not blockers and len(gates) == len(GATES)
    identity_fields = ("release_version", "hardware_revision", "radio_firmware_sha256",
                       "audio_firmware_sha256", "system_firmware_sha256", "created_utc")
    identity_complete = all(data.get(field) not in (None, "") for field in identity_fields)
    if all_gates_pass:
        for field in ("radio_firmware_sha256", "audio_firmware_sha256", "system_firmware_sha256"):
            if not SHA256.fullmatch(str(data.get(field, ""))):
                errors.append(f"{field} must be lowercase SHA-256")
        if not _utc(data.get("created_utc")):
            errors.append("created_utc must be UTC")
        if not identity_complete:
            errors.append("passing release requires complete release identity")
        if passed_tests != ALL_TESTS:
            errors.append("passing release lacks evidence coverage for AV-001 through AV-040")
    if top_status == "PASS" and (not all_gates_pass or errors):
        errors.append("top-level PASS requires every release gate and test to pass")
    if all_gates_pass and not errors and top_status != "PASS":
        errors.append("all passing gates require top-level PASS")
    return errors, blockers


def verify_artifacts(data: dict, root_path: Path) -> list[str]:
    errors: list[str] = []
    root = root_path.resolve()
    for gate in data.get("gates", []):
        for item in gate.get("evidence", []):
            path = (root / str(item.get("artifact_file", ""))).resolve()
            try:
                path.relative_to(root)
            except ValueError:
                errors.append(f"artifact escapes evidence root: {gate.get('id')}")
                continue
            if not path.is_file():
                errors.append(f"artifact is missing: {gate.get('id')}:{item.get('artifact_file')}")
                continue
            actual = hashlib.sha256(path.read_bytes()).hexdigest()
            if actual != item.get("sha256"):
                errors.append(f"artifact hash mismatch: {gate.get('id')}:{item.get('artifact_file')}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--require-release", action="store_true")
    parser.add_argument("--artifact-root", type=Path)
    args = parser.parse_args()
    data = json.loads(args.manifest.read_text(encoding="utf-8"))
    errors, blockers = validate_manifest(data)
    if args.artifact_root is not None:
        errors.extend(verify_artifacts(data, args.artifact_root))
    elif args.require_release:
        errors.append("strict release requires --artifact-root")
    for error in errors:
        print(f"ERROR: {error}")
    for blocker in blockers:
        print(f"BLOCKER: {blocker}")
    return 1 if errors or (args.require_release and blockers) else 0


if __name__ == "__main__":
    raise SystemExit(main())
