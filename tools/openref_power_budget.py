#!/usr/bin/env python3
"""Evaluate an OpenRef wearable power budget from explicit assumptions."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


VALID_EVIDENCE_CLASSES = {"assumed", "datasheet", "measured"}
MEASUREMENT_FIELDS = {"artifact_file", "sha256", "method", "instrument", "captured_utc"}


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_config(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_unique_object)


def _evidence_class(value: Any, label: str, unmeasured: list[str]) -> str:
    evidence_class = str(value)
    if evidence_class not in VALID_EVIDENCE_CLASSES:
        raise ValueError(f"invalid evidence class for {label}")
    if evidence_class != "measured":
        unmeasured.append(label)
    return evidence_class


def _measurement_is_traceable(value: Any) -> bool:
    if not isinstance(value, dict) or not MEASUREMENT_FIELDS.issubset(value):
        return False
    if any(not isinstance(value[field], str) or not value[field].strip()
           for field in MEASUREMENT_FIELDS):
        return False
    digest = value["sha256"]
    path = Path(value["artifact_file"])
    return (len(digest) == 64 and
            all(char in "0123456789abcdefABCDEF" for char in digest) and
            not path.is_absolute() and ".." not in path.parts and
            "T" in value["captured_utc"] and value["captured_utc"].endswith("Z"))


def _require_traceable_measurement(
    evidence_class: str, evidence: Any, label: str, unmeasured: list[str]
) -> None:
    if evidence_class == "measured" and not _measurement_is_traceable(evidence):
        unmeasured.append(f"{label}.traceable_evidence")


def _measurement_records(config: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    records: list[tuple[str, dict[str, Any]]] = []
    battery = config["battery"]
    if battery.get("capacity_evidence_class") == "measured":
        records.append(("battery.capacity_mah", battery.get("capacity_evidence")))
    for name, value in battery.get("factor_evidence_class", {}).items():
        if value == "measured":
            records.append((f"battery.usable_capacity_factors.{name}",
                            battery.get("factor_evidence", {}).get(name)))
    for load in config.get("loads", []):
        if load.get("evidence_class") == "measured":
            records.append((f"loads.{load.get('name')}", load.get("evidence")))
    return records


def validate_measurement_artifacts(config: dict[str, Any], evidence_root: Path) -> list[str]:
    errors: list[str] = []
    root = evidence_root.resolve()
    for label, evidence in _measurement_records(config):
        if not _measurement_is_traceable(evidence):
            errors.append(f"invalid measurement metadata: {label}")
            continue
        path = (root / evidence["artifact_file"]).resolve()
        try:
            path.relative_to(root)
        except ValueError:
            errors.append(f"measurement artifact escapes evidence root: {label}")
            continue
        if not path.is_file():
            errors.append(f"measurement artifact is missing: {label}")
            continue
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual.lower() != evidence["sha256"].lower():
            errors.append(f"measurement artifact hash mismatch: {label}")
    return errors


def evaluate(config: dict[str, Any], evidence_root: Path | None = None) -> dict[str, Any]:
    battery = config["battery"]
    voltage_v = float(battery["nominal_voltage_v"])
    capacity_mah = float(battery["capacity_mah"])
    target_h = float(config["target_endurance_h"])
    if voltage_v <= 0.0 or capacity_mah <= 0.0 or target_h <= 0.0:
        raise ValueError("battery voltage, capacity, and endurance must be positive")

    unmeasured_inputs: list[str] = []
    capacity_class = _evidence_class(
        battery.get("capacity_evidence_class", "assumed"),
        "battery.capacity_mah",
        unmeasured_inputs,
    )
    _require_traceable_measurement(
        capacity_class, battery.get("capacity_evidence"),
        "battery.capacity_mah", unmeasured_inputs,
    )
    reserve_product = 1.0
    reserve_factors: dict[str, float] = {}
    factor_evidence = battery.get("factor_evidence_class", {})
    for name, factor in battery["usable_capacity_factors"].items():
        value = float(factor)
        if not 0.0 < value <= 1.0:
            raise ValueError("usable-capacity factors must be in (0, 1]")
        reserve_product *= value
        reserve_factors[name] = value
        factor_class = _evidence_class(
            factor_evidence.get(name, "assumed"),
            f"battery.usable_capacity_factors.{name}",
            unmeasured_inputs,
        )
        _require_traceable_measurement(
            factor_class, battery.get("factor_evidence", {}).get(name),
            f"battery.usable_capacity_factors.{name}", unmeasured_inputs,
        )

    loads: list[dict[str, Any]] = []
    total_mw = 0.0
    for load in config["loads"]:
        duty = float(load.get("duty_cycle", 1.0))
        efficiency = float(load.get("conversion_efficiency", 1.0))
        if not 0.0 <= duty <= 1.0 or not 0.0 < efficiency <= 1.0:
            raise ValueError("duty must be in [0, 1] and efficiency in (0, 1]")
        if "power_mw" in load:
            rated_mw = float(load["power_mw"])
            if rated_mw < 0.0:
                raise ValueError("load power must be nonnegative")
            rail_mw = rated_mw * duty
        else:
            load_voltage = float(load["voltage_v"])
            load_current = float(load["current_ma"])
            if load_voltage < 0.0 or load_current < 0.0:
                raise ValueError("load voltage and current must be nonnegative")
            rail_mw = load_voltage * load_current * duty
        evidence_class = _evidence_class(
            load.get("evidence_class", "assumed"),
            f"loads.{load['name']}",
            unmeasured_inputs,
        )
        _require_traceable_measurement(
            evidence_class, load.get("evidence"), f"loads.{load['name']}",
            unmeasured_inputs,
        )
        battery_mw = rail_mw / efficiency
        total_mw += battery_mw
        loads.append({
            "name": load["name"],
            "evidence": load["evidence"],
            "evidence_class": evidence_class,
            "rail_mw": round(rail_mw, 3),
            "battery_mw": round(battery_mw, 3),
        })

    if total_mw <= 0.0:
        raise ValueError("total average load must be positive")
    nominal_wh = voltage_v * capacity_mah / 1000.0
    usable_wh = nominal_wh * reserve_product
    endurance_h = usable_wh * 1000.0 / total_mw
    required_usable_wh = total_mw * target_h / 1000.0
    required_nominal_mah = required_usable_wh / (voltage_v * reserve_product) * 1000.0
    maximum_average_mw = usable_wh * 1000.0 / target_h
    artifact_errors = (validate_measurement_artifacts(config, evidence_root)
                       if evidence_root is not None else [])
    return {
        "name": config["name"],
        "status": config["status"],
        "total_average_mw": round(total_mw, 3),
        "nominal_battery_wh": round(nominal_wh, 3),
        "usable_battery_wh": round(usable_wh, 3),
        "usable_capacity_fraction": round(reserve_product, 5),
        "usable_capacity_factors": reserve_factors,
        "estimated_endurance_h": round(endurance_h, 3),
        "target_endurance_h": target_h,
        "target_margin_h": round(endurance_h - target_h, 3),
        "maximum_average_mw_at_target": round(maximum_average_mw, 3),
        "load_headroom_factor": round(maximum_average_mw / total_mw, 3),
        "required_nominal_capacity_mah": round(required_nominal_mah, 1),
        "release_ready": not unmeasured_inputs and evidence_root is not None and not artifact_errors,
        "measurement_metadata_complete": not unmeasured_inputs,
        "measurement_artifacts_verified": evidence_root is not None and not artifact_errors,
        "artifact_errors": artifact_errors,
        "unmeasured_inputs": unmeasured_inputs,
        "loads": loads,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate an OpenRef power budget")
    parser.add_argument("config", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--evidence-root", type=Path)
    parser.add_argument("--require-release", action="store_true")
    args = parser.parse_args()
    result = evaluate(load_config(args.config), args.evidence_root)
    rendered = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    if args.require_release and not result["release_ready"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
