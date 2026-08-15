#!/usr/bin/env python3
"""Validate the wearable mechanical interface and report physical-input blockers."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


REQUIRED_ZONES = {"ANTENNA", "BATTERY", "AUDIO_ANALOG", "USER_CONTROLS", "SERVICE_ACCESS"}
REQUIRED_INTERFACES = {"BATTERY", "HEADSET", "CONTROLS", "SERVICE", "MOUNT"}
REQUIRED_TESTS = {"AV-015", "AV-016", "AV-017", "AV-018", "AV-019", "AV-036"}
SAFETY_KEYS = {
    "no_sharp_edges_normal_or_damaged", "battery_cannot_become_projectile",
    "antenna_clearance_preserved_when_worn", "headset_load_not_transferred_to_pcb_joint",
    "service_contacts_inaccessible_during_wear",
    "vents_or_openings_do_not_drain_into_electronics",
}
DECISION_FIELDS = {
    "product_configuration.wear_location",
    "product_configuration.mounting_orientation",
    "product_configuration.maximum_envelope_mm.x",
    "product_configuration.maximum_envelope_mm.y",
    "product_configuration.maximum_envelope_mm.z",
    "product_configuration.target_mass_g",
    "product_configuration.minimum_sealing_objective",
    "product_configuration.service_configuration_defined",
    "placement_decisions.antenna_location",
    "placement_decisions.battery_location",
    "placement_decisions.headset_connector_location",
    "placement_decisions.control_location",
    "placement_decisions.status_visibility_direction",
}


def _lookup(data: dict, dotted: str):
    value = data
    for part in dotted.split("."):
        value = value.get(part) if isinstance(value, dict) else None
    return value


def validate_contract(data: dict) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    blockers: list[str] = []
    if data.get("document_id") != "OR-HW-009" or data.get("revision", 0) < 1:
        errors.append("invalid document identity or revision")
    zones = {zone.get("id"): zone for zone in data.get("zones", [])}
    if set(zones) != REQUIRED_ZONES:
        errors.append("zones must exactly match the controlled zone set")
    for zone in zones.values():
        if zone.get("required") is not True or not zone.get("dimensions_source"):
            errors.append(f"zone {zone.get('id')} lacks requirement or dimension source")
    if "BATTERY" not in zones.get("ANTENNA", {}).get("excludes", []) or \
       "ANTENNA" not in zones.get("BATTERY", {}).get("excludes", []):
        errors.append("antenna and battery zones must exclude each other")
    for excluded in ("SWITCHING_POWER", "HAPTIC", "HIGH_EDGE_DIGITAL"):
        if excluded not in zones.get("AUDIO_ANALOG", {}).get("excludes", []):
            errors.append(f"audio analog zone must exclude {excluded}")

    interfaces = {item.get("id"): item for item in data.get("interfaces", [])}
    if set(interfaces) != REQUIRED_INTERFACES:
        errors.append("interfaces must exactly match the controlled interface set")
    required_true = {
        "BATTERY": ("removable", "external_charging_only", "polarized", "retention_required", "seal_boundary_required"),
        "HEADSET": ("replaceable", "strain_relief_required", "wet_mate_behavior_tested", "seal_boundary_required"),
        "CONTROLS": ("wet_glove_operable", "accidental_activation_tested", "seal_boundary_required"),
        "SERVICE": ("wearer_inaccessible", "fixture_accessible", "seal_restored_after_service"),
        "MOUNT": ("running_retention_tested", "direction_change_tested", "breakaway_decision_required"),
    }
    for interface, keys in required_true.items():
        for key in keys:
            if interfaces.get(interface, {}).get(key) is not True:
                errors.append(f"{interface}.{key} must remain required")
    safety = data.get("safety_constraints", {})
    if set(safety) != SAFETY_KEYS or any(safety.get(key) is not True for key in SAFETY_KEYS):
        errors.append("all controlled mechanical safety constraints must be present and true")
    tests = {item.get("test_id") for item in data.get("required_verification", [])}
    if tests != REQUIRED_TESTS:
        errors.append("required verification must exactly cover AV-015/016/017/018/019/036")

    for field in sorted(DECISION_FIELDS):
        value = _lookup(data, field)
        if value is None or value is False or value == "":
            blockers.append(field)
    dimensions = data.get("product_configuration", {}).get("maximum_envelope_mm", {})
    for axis in ("x", "y", "z"):
        value = dimensions.get(axis)
        if value is not None and (not isinstance(value, (int, float)) or isinstance(value, bool) or value <= 0):
            errors.append(f"maximum_envelope_mm.{axis} must be null or positive")
    mass = data.get("product_configuration", {}).get("target_mass_g")
    if mass is not None and (not isinstance(mass, (int, float)) or isinstance(mass, bool) or mass <= 0):
        errors.append("target_mass_g must be null or positive")
    return errors, blockers


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("contract", type=Path)
    parser.add_argument("--require-release", action="store_true")
    args = parser.parse_args()
    data = json.loads(args.contract.read_text(encoding="utf-8"))
    errors, blockers = validate_contract(data)
    for error in errors:
        print(f"ERROR: {error}")
    for blocker in blockers:
        print(f"BLOCKER: {blocker}")
    return 1 if errors or (args.require_release and blockers) else 0


if __name__ == "__main__":
    raise SystemExit(main())
