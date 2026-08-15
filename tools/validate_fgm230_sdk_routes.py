#!/usr/bin/env python3
"""Validate OR-HW-006 routes against Silicon Labs FGM230SB SDK metadata."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


EXPECTED_ROUTES = {
    ("USART0", "CLK"): ("PB00", "AUD_SCLK"),
    ("USART0", "CS"): ("PB01", "AUD_CSN"),
    ("USART0", "TX"): ("PA07", "AUD_COPI"),
    ("USART0", "RX"): ("PA08", "AUD_CIPO"),
    ("EUSART0", "TX"): ("PA04", "RADIO_UART_TX"),
    ("EUSART0", "RX"): ("PA05", "RADIO_UART_RX"),
    ("IADC0", "POS"): ("PA00", "ACCESSORY_ID_ADC"),
    ("LFXO", "LFXTAL_I"): ("PD01", "LFXO_IN_OPTION"),
    ("LFXO", "LFXTAL_O"): ("PD00", "LFXO_OUT_OPTION"),
}
PORT_MASKS = {"A": 0x07FF, "B": 0x007F, "C": 0x03FF, "D": 0x003F}
FIXED_DEBUG = {"SWCLK": "PA01", "SWDIO": "PA02", "SWV": "PA03"}


def macro_int(text: str, name: str) -> int | None:
    match = re.search(rf"^#define\s+{re.escape(name)}\s+\(?0x([0-9A-Fa-f]+)", text, re.MULTILINE)
    if match:
        return int(match.group(1), 16)
    match = re.search(rf"^#define\s+{re.escape(name)}\s+(\d+)U?\b", text, re.MULTILINE)
    return int(match.group(1)) if match else None


def validate_routes(allocation: dict, device_header: str, gpio_header: str,
                    iadc_header: str) -> list[str]:
    errors: list[str] = []
    pins = {pin["pad"]: pin["net"] for pin in allocation.get("pins", [])}
    routes = {
        (route.get("peripheral"), route.get("signal")): (route.get("pad"), route.get("net"))
        for route in allocation.get("peripheral_routes", [])
    }
    if routes != EXPECTED_ROUTES:
        errors.append("peripheral_routes must exactly match the controlled route set")
    for key, (pad, net) in EXPECTED_ROUTES.items():
        if pins.get(pad) != net:
            errors.append(f"{key[0]} {key[1]} route does not match package allocation")

    for port, expected in PORT_MASKS.items():
        actual = macro_int(device_header, f"GPIO_P{port}_MASK")
        if actual != expected:
            errors.append(f"SDK GPIO_P{port}_MASK is {actual!r}, expected 0x{expected:04X}")
    port_indexes = {port: macro_int(device_header, f"GPIO_P{port}_INDEX") for port in PORT_MASKS}
    for signal, pad in FIXED_DEBUG.items():
        port = pad[1]
        pin = int(pad[2:])
        port_macro = re.search(
            rf"^#define\s+GPIO_{signal}_PORT\s+GPIO_P([A-D])_INDEX\b",
            device_header, re.MULTILINE,
        )
        if not port_macro or port_macro.group(1) != port:
            errors.append(f"SDK fixed {signal} port does not match {pad}")
        if macro_int(device_header, f"GPIO_{signal}_PIN") != pin:
            errors.append(f"SDK fixed {signal} pin does not match {pad}")
    del port_indexes  # Presence is established by mask checks above.

    for name, minimum in (("USART_COUNT", 1), ("EUSART_COUNT", 1), ("IADC_COUNT", 1)):
        value = macro_int(device_header, name)
        if value is None or value < minimum:
            errors.append(f"SDK does not expose required {name}")
    fixed_lfxo = {"LFXTAL_I": "PD01", "LFXTAL_O": "PD00"}
    for signal, pad in fixed_lfxo.items():
        port_match = re.search(
            rf"^#define\s+LFXO_{signal}_PORT\s+GPIO_P([A-D])_INDEX\b",
            device_header, re.MULTILINE,
        )
        pin_number = macro_int(device_header, f"LFXO_{signal}_PIN")
        actual_pad = (
            f"P{port_match.group(1)}{pin_number:02d}"
            if port_match and pin_number is not None else None
        )
        if actual_pad != pad:
            errors.append(f"SDK fixed LFXO {signal} does not match {pad}")
    for register in ("CSROUTE", "RXROUTE", "CLKROUTE", "TXROUTE"):
        if register not in gpio_header:
            errors.append(f"SDK GPIO route metadata lacks USART {register}")
    if "iadcPosInputPortAPin0" not in iadc_header:
        errors.append("SDK emlib does not expose PA00 as an IADC positive input")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("allocation", type=Path)
    parser.add_argument("sdk_root", type=Path)
    args = parser.parse_args()
    root = args.sdk_root
    include = root / "platform_core/platform/Device/SiliconLabs/FGM23/Include"
    errors = validate_routes(
        json.loads(args.allocation.read_text(encoding="utf-8")),
        (include / "fgm230sb27hgn.h").read_text(encoding="utf-8"),
        (include / "fgm23_gpio.h").read_text(encoding="utf-8"),
        (root / "platform_core/platform/emlib/inc/em_iadc.h").read_text(encoding="utf-8"),
    )
    for error in errors:
        print(f"ERROR: {error}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
