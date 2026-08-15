#!/usr/bin/env python3
"""Cross-check the Prototype 1 functional connectivity against controlled contracts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


REQUIRED_BLOCKS = {
    "PACK", "INPUT_PROTECTION", "SYSTEM_SWITCH", "ALWAYS_ON", "RADIO_REG",
    "AUDIO_REG", "CODEC_REG", "FGM230", "AUDIO_PROCESSOR", "CODEC",
    "MIC_BIAS_SENSE", "OUTPUT_LIMIT_MUTE", "HEADSET_PROTECTION", "HEADSET",
    "LINK_ISOLATION", "LINK_TEST", "RF_BOUNDARY", "ANTENNA",
}
REQUIRED_POWER_CHAIN = {
    "VBAT_PROTECTED": ("PACK", {"INPUT_PROTECTION"}),
    "VSYS_BLOCKED": ("INPUT_PROTECTION", {"SYSTEM_SWITCH", "ALWAYS_ON"}),
    "V_ALWAYS_ON": ("SYSTEM_SWITCH", {"ALWAYS_ON", "RADIO_REG", "AUDIO_REG", "CODEC_REG"}),
    "V_RADIO": ("RADIO_REG", {"FGM230"}),
    "V_AUDIO": ("AUDIO_REG", {"AUDIO_PROCESSOR"}),
    "V_CODEC": ("CODEC_REG", {"CODEC", "MIC_BIAS_SENSE", "OUTPUT_LIMIT_MUTE"}),
}
CRITICAL_AUDIO = {
    "MIC_AUDIO": ("HEADSET", ["HEADSET_PROTECTION", "MIC_BIAS_SENSE"], "CODEC"),
    "EARPIECE_AUDIO": ("CODEC", ["OUTPUT_LIMIT_MUTE", "HEADSET_PROTECTION"], "HEADSET"),
}


def validate_connectivity(graph: dict, contract: dict, allocation: dict) -> list[str]:
    errors: list[str] = []
    if graph.get("document_id") != "OR-HW-008" or graph.get("revision", 0) < 1:
        errors.append("invalid connectivity document identity or revision")
    blocks = {block.get("id"): block for block in graph.get("blocks", [])}
    for missing in sorted(REQUIRED_BLOCKS - blocks.keys()):
        errors.append(f"required block is missing: {missing}")
    valid_sheets = {sheet["id"] for sheet in contract.get("sheets", [])}
    for block in blocks.values():
        if block.get("sheet") not in valid_sheets:
            errors.append(f"block {block.get('id')} has invalid sheet")
        if block.get("selection") not in {
            "selected", "pending", "pending_benchmark", "pending_mechanical",
            "pending_antenna", "pending_body_test", "interface_selected",
        }:
            errors.append(f"block {block.get('id')} lacks an explicit selection state")

    power = {path.get("net"): path for path in graph.get("power_paths", [])}
    contract_domains = {domain["name"] for domain in contract.get("power_domains", [])}
    if set(power) != contract_domains:
        errors.append("power paths must exactly cover the electrical-contract domains")
    for net, (source, required_sinks) in REQUIRED_POWER_CHAIN.items():
        path = power.get(net, {})
        if path.get("source") != source or not required_sinks.issubset(set(path.get("sinks", []))):
            errors.append(f"{net} does not implement its required source/sink topology")
    for net, path in power.items():
        if not path.get("current_link") or not path.get("test_point"):
            errors.append(f"{net} requires a current link and test point")
        for endpoint in [path.get("source"), *path.get("sinks", [])]:
            if endpoint not in blocks:
                errors.append(f"{net} references unknown block {endpoint}")

    signals = {path.get("net"): path for path in graph.get("signal_paths", [])}
    contract_signals = {signal["name"]: signal for signal in contract.get("signals", [])}
    for net, controlled in contract_signals.items():
        path = signals.get(net)
        if path is None:
            errors.append(f"controlled signal is absent from connectivity: {net}")
            continue
        if controlled.get("isolation_required") and "LINK_ISOLATION" not in path.get("via", []):
            errors.append(f"{net} requires LINK_ISOLATION")
        if controlled.get("test_access") and not path.get("test_point"):
            errors.append(f"{net} requires test access")
    allocation_nets = {pin.get("net") for pin in allocation.get("pins", [])}
    for net in ("AUD_SCLK", "AUD_COPI", "AUD_CIPO", "AUD_CSN", "AUD_REQ_N", "AUD_RESET_N", "RADIO_RESET_REQ_N", "RADIO_RESET_N", "RF_50OHM"):
        if net not in allocation_nets or net not in signals:
            errors.append(f"FGM230 connectivity is not reconciled for {net}")
    for net in ("AUD_SCLK", "AUD_COPI"):
        if not signals.get(net, {}).get("series_source_footprint"):
            errors.append(f"{net} requires a source-series footprint")
    if signals.get("AUD_RESET_N", {}).get("hardware_bias") != "asserted_low_if_either_domain_off":
        errors.append("AUD_RESET_N lacks its mandatory fail-safe hardware bias")
    for net, (source, via, sink) in CRITICAL_AUDIO.items():
        path = signals.get(net, {})
        if path.get("source") != source or path.get("via") != via or sink not in path.get("sinks", []):
            errors.append(f"{net} does not implement the controlled safety path")
    if not signals.get("EARPIECE_AUDIO", {}).get("dummy_load_before_human"):
        errors.append("earpiece output requires dummy-load bring-up before human listening")
    rf = signals.get("RF_50OHM", {})
    if rf.get("source") != "FGM230" or rf.get("via") != ["RF_BOUNDARY"] or rf.get("sinks") != ["ANTENNA"]:
        errors.append("RF_50OHM must traverse the RF boundary to the antenna")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("connectivity", type=Path)
    parser.add_argument("contract", type=Path)
    parser.add_argument("allocation", type=Path)
    args = parser.parse_args()
    load = lambda path: json.loads(path.read_text(encoding="utf-8"))
    errors = validate_connectivity(load(args.connectivity), load(args.contract), load(args.allocation))
    for error in errors:
        print(f"ERROR: {error}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
