#!/usr/bin/env python3
"""Validate the controlled Prototype 1 pre-schematic connectivity contract."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


REQUIRED_SHEETS = {f"{number:02d}" for number in range(1, 9)}
REQUIRED_DOMAINS = {
    "VBAT_PROTECTED", "VSYS_BLOCKED", "V_ALWAYS_ON", "V_RADIO",
    "V_AUDIO", "V_CODEC", "V_HAPTIC",
}
REQUIRED_LINK_SIGNALS = {
    "AUD_SCLK", "AUD_COPI", "AUD_CIPO", "AUD_CSN", "AUD_REQ_N",
    "AUD_RESET_N", "RADIO_RESET_REQ_N",
}
SAFE_RESET_STATES = {"low", "high", "high_z"}
FIXED_SIGNAL_POLICIES = {
    "AUD_SCLK": ("03", "04", "V_RADIO", "V_AUDIO", "low"),
    "AUD_COPI": ("03", "04", "V_RADIO", "V_AUDIO", "low"),
    "AUD_CIPO": ("04", "03", "V_AUDIO", "V_RADIO", "high_z"),
    "AUD_CSN": ("03", "04", "V_RADIO", "V_AUDIO", "high"),
    "AUD_REQ_N": ("04", "03", "V_AUDIO", "V_RADIO", "high"),
    "AUD_RESET_N": ("03", "04", "V_RADIO", "V_AUDIO", "low"),
    "RADIO_RESET_REQ_N": ("04", "03", "V_AUDIO", "V_RADIO", "high"),
}


def validate_contract(data: dict) -> list[str]:
    errors: list[str] = []
    if data.get("contract_id") != "OR-HW-005" or data.get("revision", 0) < 1:
        errors.append("contract identity or revision is invalid")

    sheets = data.get("sheets", [])
    sheet_ids = [sheet.get("id") for sheet in sheets]
    if len(sheet_ids) != len(set(sheet_ids)):
        errors.append("sheet IDs must be unique")
    if set(sheet_ids) != REQUIRED_SHEETS:
        errors.append("contract must define sheets 01 through 08 exactly")

    domains = data.get("power_domains", [])
    domain_names = [domain.get("name") for domain in domains]
    if len(domain_names) != len(set(domain_names)):
        errors.append("power-domain names must be unique")
    if set(domain_names) != REQUIRED_DOMAINS:
        errors.append("required named power domains are incomplete")
    for domain in domains:
        if domain.get("owner_sheet") not in REQUIRED_SHEETS:
            errors.append(f"domain {domain.get('name')} has an invalid owner")
        if not isinstance(domain.get("switched"), bool):
            errors.append(f"domain {domain.get('name')} lacks switched policy")

    signals = data.get("signals", [])
    signal_names = [signal.get("name") for signal in signals]
    if len(signal_names) != len(set(signal_names)):
        errors.append("signal names must be unique")
    missing = REQUIRED_LINK_SIGNALS - set(signal_names)
    if missing:
        errors.append(f"processor link is missing: {', '.join(sorted(missing))}")
    domain_set = set(domain_names)
    for signal in signals:
        name = signal.get("name", "<unnamed>")
        if signal.get("source") not in REQUIRED_SHEETS or signal.get("sink") not in REQUIRED_SHEETS:
            errors.append(f"signal {name} has an invalid sheet endpoint")
        if signal.get("source_domain") not in domain_set or signal.get("sink_domain") not in domain_set:
            errors.append(f"signal {name} has an invalid power domain")
        if signal.get("reset_state") not in SAFE_RESET_STATES:
            errors.append(f"signal {name} lacks an explicit safe reset state")
        if signal.get("source_domain") != signal.get("sink_domain") and "isolation_required" not in signal:
            errors.append(f"cross-domain signal {name} lacks isolation policy")
        if not isinstance(signal.get("test_access"), bool):
            errors.append(f"signal {name} lacks test-access policy")
        if name in FIXED_SIGNAL_POLICIES:
            actual = tuple(signal.get(field) for field in (
                "source", "sink", "source_domain", "sink_domain", "reset_state"
            ))
            if actual != FIXED_SIGNAL_POLICIES[name]:
                errors.append(f"signal {name} violates the fixed processor-link policy")
            if signal.get("isolation_required") is not True:
                errors.append(f"signal {name} requires cross-domain isolation")

    test_points = data.get("required_test_points", [])
    if len(test_points) != len(set(test_points)):
        errors.append("required test-point names must be unique")
    for name in REQUIRED_DOMAINS | REQUIRED_LINK_SIGNALS:
        if name not in test_points:
            errors.append(f"required test point is missing: {name}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("contract", type=Path)
    args = parser.parse_args()
    errors = validate_contract(json.loads(args.contract.read_text(encoding="utf-8")))
    for error in errors:
        print(f"ERROR: {error}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
