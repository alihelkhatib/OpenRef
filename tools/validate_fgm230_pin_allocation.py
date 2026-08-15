#!/usr/bin/env python3
"""Validate the controlled FGM230SB Prototype 1 package-pin allocation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


CANONICAL_PADS = {
    1: "RESETn", 2: "GND", 3: "RFIO", 4: "GND", 5: "PB06", 6: "PB05",
    7: "PB04", 8: "PB03", 9: "PB02", 10: "PB01", 11: "PB00",
    12: "PA00", 13: "PA01", 14: "PA02", 15: "PA03", 16: "PA04",
    17: "PA05", 18: "DECOUPLE", 19: "PA06", 20: "PA07", 21: "PA08",
    22: "PA09", 23: "PA10", 24: "VDCDC", 25: "VREGVDD", 26: "IOVDD",
    27: "GND", 28: "PD05", 29: "PD04", 30: "PD03", 31: "PD02",
    32: "PD01", 33: "PD00", 34: "PC00", 35: "PC01", 36: "PC02",
    37: "PC03", 38: "PC04", 39: "PC05", 40: "PC06", 41: "PC07",
    42: "PC08", 43: "PC09", 44: "GND", 45: "GND", 46: "GND",
    47: "GND", 48: "GND",
}
FIXED_NETS = {
    "PA01": "RADIO_SWCLK", "PA02": "RADIO_SWDIO", "PA03": "RADIO_SWO",
    "PB03": "AUD_RESET_N", "PB02": "AUD_REQ_N", "PB01": "AUD_CSN",
    "PB00": "AUD_SCLK", "PA07": "AUD_COPI", "PA08": "AUD_CIPO",
    "RESETn": "RADIO_RESET_N", "RFIO": "RF_50OHM",
    "DECOUPLE": "NC_DECOUPLE", "VDCDC": "NC_VDCDC",
}
REQUIRED_NETS = set(FIXED_NETS.values()) | {
    "V_RADIO", "GND", "RADIO_UART_TX", "RADIO_UART_RX", "RADIO_TX_START",
    "RADIO_PTI_FRAME", "RADIO_PTI_DATA", "CREW_JOIN_BUTTON_N",
    "VOLUME_UP_N", "VOLUME_DOWN_N", "HAPTIC_EN", "ACCESSORY_ID_ADC",
    "ACCESSORY_PRESENT_N", "POWER_ALERT_N",
}


def validate_allocation(data: dict) -> list[str]:
    errors: list[str] = []
    if data.get("document_id") != "OR-HW-006" or data.get("revision", 0) < 1:
        errors.append("invalid document identity or revision")
    if data.get("ordering_code") != "FGM230SB27HGN3":
        errors.append("allocation targets the wrong ordering code")
    pins = data.get("pins", [])
    numbers = [entry.get("pin") for entry in pins]
    if len(numbers) != 48 or set(numbers) != set(CANONICAL_PADS):
        errors.append("all package pins 1 through 48 must appear exactly once")
    by_pad: dict[str, dict] = {}
    for entry in pins:
        number = entry.get("pin")
        pad = entry.get("pad")
        if number in CANONICAL_PADS and pad != CANONICAL_PADS[number]:
            errors.append(f"pin {number} must be {CANONICAL_PADS[number]}, not {pad}")
        if pad not in {"GND"}:
            if pad in by_pad:
                errors.append(f"pad {pad} appears more than once")
            by_pad[pad] = entry
        for field in ("net", "direction", "safe_state", "class"):
            if not isinstance(entry.get(field), str) or not entry[field]:
                errors.append(f"pin {number} lacks {field}")
    for pad, net in FIXED_NETS.items():
        if by_pad.get(pad, {}).get("net") != net:
            errors.append(f"{pad} must be allocated to {net}")
    for entry in pins:
        if entry.get("pad") == "GND" and entry.get("net") != "GND":
            errors.append(f"ground pin {entry.get('pin')} is not connected to GND")
        if entry.get("pad") in {"DECOUPLE", "VDCDC"} and (
            entry.get("net") != FIXED_NETS[entry["pad"]] or
            entry.get("direction") != "no_connect" or
            entry.get("safe_state") != "no_connect"
        ):
            errors.append(f"{entry.get('pad')} must be an explicit no-connect")
        if entry.get("pad") in {"VREGVDD", "IOVDD"} and (
            entry.get("net") != "V_RADIO" or
            entry.get("safe_state") != "decoupled_10uf"
        ):
            errors.append(f"{entry.get('pad')} requires V_RADIO and 10 uF decoupling")
    nets = {entry.get("net") for entry in pins}
    for net in sorted(REQUIRED_NETS - nets):
        errors.append(f"required net is missing: {net}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("allocation", type=Path)
    args = parser.parse_args()
    data = json.loads(args.allocation.read_text(encoding="utf-8"))
    errors = validate_allocation(data)
    for error in errors:
        print(f"ERROR: {error}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
