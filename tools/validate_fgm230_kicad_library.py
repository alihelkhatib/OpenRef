#!/usr/bin/env python3
"""Validate generated FGM230SB KiCad library content and geometry."""

from __future__ import annotations

import csv
import re
from pathlib import Path

from generate_fgm230_kicad_library import (
    CAD,
    CSV,
    FOOTPRINT,
    SYMBOL,
    generate_footprint,
    generate_symbol,
    pad_position,
)


NUMBERED_PAD_RE = re.compile(
    r'\(pad "(\d+)" smd rect \(at (-?\d+\.\d+) (-?\d+\.\d+)\) '
    r'\(size (\d+\.\d+) (\d+\.\d+)\) \(layers "F\.Cu" "F\.Mask"\)\)'
)
PASTE_PAD_RE = re.compile(
    r'\(pad "" smd rect \(at (-?\d+\.\d+) (-?\d+\.\d+)\) '
    r'\(size (\d+\.\d+) (\d+\.\d+)\) \(layers "F\.Paste"\)\)'
)
SYMBOL_PIN_RE = re.compile(
    r'\(pin \w+ line .*?\(name "([^"]+)" .*?\(number "(\d+)"'
)


def balanced_sexpression(text: str) -> bool:
    depth = 0
    quoted = False
    escaped = False
    for char in text:
        if quoted:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                quoted = False
        elif char == '"':
            quoted = True
        elif char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth < 0:
                return False
    return depth == 0 and not quoted


def validate_library() -> list[str]:
    errors: list[str] = []
    with CSV.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    symbol = SYMBOL.read_text(encoding="utf-8")
    footprint = FOOTPRINT.read_text(encoding="utf-8")

    if not balanced_sexpression(symbol):
        errors.append("symbol S-expression is unbalanced")
    if not balanced_sexpression(footprint):
        errors.append("footprint S-expression is unbalanced")
    if symbol != generate_symbol(rows):
        errors.append("symbol differs from reproducible generator output")
    if footprint != generate_footprint():
        errors.append("footprint differs from reproducible generator output")

    pins = [(int(number), name) for name, number in SYMBOL_PIN_RE.findall(symbol)]
    expected_pins = [(int(row["pin"]), row["pad"]) for row in rows]
    if pins != expected_pins:
        errors.append("symbol pin number/name mapping differs from controlled CSV")

    pads = NUMBERED_PAD_RE.findall(footprint)
    if [int(pad[0]) for pad in pads] != list(range(1, 49)):
        errors.append("footprint must contain numbered pads 1 through 48 exactly once")
    else:
        for number_text, x, y, sx, sy in pads:
            expected = pad_position(int(number_text))
            actual = tuple(float(value) for value in (x, y, sx, sy))
            if actual != expected:
                errors.append(f"pad {number_text} geometry differs from Figure 8.4")

    paste = PASTE_PAD_RE.findall(footprint)
    if len(paste) != 48:
        errors.append("footprint must contain one paste aperture per copper pad")
    else:
        for index, values in enumerate(paste, start=1):
            x, y, sx, sy = (float(value) for value in values)
            px, py, copper_x, copper_y = pad_position(index)
            if (x, y) != (px, py):
                errors.append(f"paste aperture {index} is not centered on its pad")
            area_ratio = sx * sy / (copper_x * copper_y)
            if abs(area_ratio - 0.80) > 0.001:
                errors.append(f"paste aperture {index} is not 80% area")
    return errors


def main() -> None:
    errors = validate_library()
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        raise SystemExit(1)
    print(f"PASS: {SYMBOL.relative_to(CAD)} and {FOOTPRINT.relative_to(CAD)}")


if __name__ == "__main__":
    main()
