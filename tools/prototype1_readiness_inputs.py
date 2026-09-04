#!/usr/bin/env python3
"""Create and validate fail-closed Prototype 1 readiness-input manifests."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

SCHEMA = "openref-prototype1-readiness-inputs-v1"
INPUTS = {
    "scheduled_tx_timing": "E0-03 scheduled TX timing measured",
    "secured_packet_airtime": "Measured secured-packet airtime supports the six-node schedule",
    "radio_mode_current": "TX, RX, idle, and continuous-packet current measured",
    "role_current_estimate": "Coordinator and member current estimate",
    "wearable_volume": "Approximate wearable volume target",
    "mounting_orientation": "Mounting orientation",
    "battery_placement": "Battery placement concept",
    "headset_connector_placement": "Headset connector placement concept",
    "control_placement": "Control placement concept",
}
PLACEHOLDERS = re.compile(r"(?i)\b(?:todo|tbd|unknown|placeholder|yyyy(?:-?mm(?:-?dd)?)?)\b")


def template() -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "inputs": [
            {"id": input_id, "label": label, "status": "open"}
            for input_id, label in INPUTS.items()
        ],
    }


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate(data: Any, manifest_path: Path) -> list[str]:
    failures: list[str] = []
    if not isinstance(data, dict):
        return ["manifest root must be a JSON object"]
    if data.get("schema") != SCHEMA:
        failures.append(f"schema must equal {SCHEMA!r}")
    items = data.get("inputs")
    if not isinstance(items, list):
        return failures + ["inputs must be a list"]
    by_id: dict[str, tuple[int, dict[str, Any]]] = {}
    for index, item in enumerate(items):
        prefix = f"inputs[{index}]"
        if not isinstance(item, dict):
            failures.append(f"{prefix} must be a JSON object")
            continue
        input_id = item.get("id")
        if input_id not in INPUTS:
            failures.append(f"{prefix}.id is not a recognized readiness input")
            continue
        if input_id in by_id:
            failures.append(f"duplicate readiness input {input_id!r}")
            continue
        by_id[input_id] = (index, item)
    for input_id in INPUTS:
        if input_id not in by_id:
            failures.append(f"missing readiness input {input_id!r}")
    for input_id, (index, item) in by_id.items():
        prefix = f"inputs[{index}]"
        expected_label = INPUTS[input_id]
        if item.get("label") != expected_label:
            failures.append(f"{prefix}.label must equal {expected_label!r}")
        status = item.get("status")
        if status not in {"open", "verified"}:
            failures.append(f"{prefix}.status must equal 'open' or 'verified'")
            continue
        if status == "open":
            failures.append(f"{prefix} ({input_id}) remains open")
            continue
        value = item.get("value")
        if not isinstance(value, dict) or not value:
            failures.append(f"{prefix}.value must be a non-empty JSON object")
        elif PLACEHOLDERS.search(json.dumps(value, sort_keys=True)):
            failures.append(f"{prefix}.value contains placeholder text")
        approved_by = item.get("approved_by")
        if not isinstance(approved_by, str) or not approved_by.strip():
            failures.append(f"{prefix}.approved_by must be non-empty")
        recorded_at = item.get("recorded_at")
        try:
            parsed = datetime.fromisoformat(recorded_at.replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                raise ValueError
        except (AttributeError, TypeError, ValueError):
            failures.append(f"{prefix}.recorded_at must be an ISO-8601 timestamp with timezone")
        evidence = item.get("evidence")
        if not isinstance(evidence, list) or not evidence:
            failures.append(f"{prefix}.evidence must be a non-empty list")
            continue
        for evidence_index, artifact in enumerate(evidence):
            artifact_prefix = f"{prefix}.evidence[{evidence_index}]"
            if not isinstance(artifact, dict):
                failures.append(f"{artifact_prefix} must be a JSON object")
                continue
            path_text = artifact.get("path")
            expected_hash = artifact.get("sha256")
            if not isinstance(path_text, str) or not path_text:
                failures.append(f"{artifact_prefix}.path must be non-empty")
                continue
            if not isinstance(expected_hash, str) or re.fullmatch(r"[0-9a-f]{64}", expected_hash) is None:
                failures.append(f"{artifact_prefix}.sha256 must be 64 lowercase hex digits")
                continue
            path = Path(path_text)
            if not path.is_absolute():
                path = manifest_path.parent / path
            try:
                actual_hash = _sha256(path)
            except OSError as error:
                failures.append(f"{artifact_prefix} cannot be read: {error}")
                continue
            if actual_hash != expected_hash:
                failures.append(f"{artifact_prefix}.sha256 does not match current file")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--template", action="store_true")
    mode.add_argument("--check", action="store_true")
    parser.add_argument("--json", type=Path, required=True)
    args = parser.parse_args()
    if args.template:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(template(), indent=2) + "\n", encoding="utf-8")
        print(args.json)
        return 0
    try:
        data = json.loads(args.json.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        print(f"cannot load readiness inputs: {error}", file=sys.stderr)
        return 2
    failures = validate(data, args.json)
    report = {
        "schema": SCHEMA,
        "manifest": str(args.json),
        "passed": not failures,
        "verified": sum(
            1 for item in data.get("inputs", [])
            if isinstance(item, dict) and item.get("status") == "verified"
        ) if isinstance(data, dict) else 0,
        "required": len(INPUTS),
        "failures": failures,
    }
    print(json.dumps(report, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
