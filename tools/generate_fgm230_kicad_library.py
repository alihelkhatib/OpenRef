#!/usr/bin/env python3
"""Generate the controlled FGM230SB KiCad symbol and footprint."""

from __future__ import annotations

import csv
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CAD = ROOT / "hardware" / "prototype1-wearable" / "cad"
CSV = CAD / "fgm230sb-symbol-pins.csv"
SYMBOL = CAD / "openref-fgm230sb.kicad_sym"
FOOTPRINT = CAD / "OpenRef-FGM230SB.pretty" / "FGM230SB27HGN3.kicad_mod"


def q(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def electrical_type(direction: str) -> str:
    return {
        "input": "input",
        "output": "output",
        "bidirectional": "bidirectional",
        "analog_input": "input",
        "analog": "passive",
        "power": "power_in",
        "rf": "passive",
        "unused": "bidirectional",
        "no_connect": "no_connect",
    }[direction]


def generate_symbol(rows: list[dict[str, str]]) -> str:
    lines = [
        '(kicad_symbol_lib (version 20231120) (generator "openref")',
    ]
    # Insert the symbol before the library's final parenthesis.
    body = [
        '  (symbol "FGM230SB27HGN3"',
        '    (pin_names (offset 1.0))',
        '    (exclude_from_sim no)',
        '    (in_bom yes)',
        '    (on_board yes)',
        '    (property "Reference" "U" (at 0 34 0) (effects (font (size 1.27 1.27))))',
        '    (property "Value" "FGM230SB27HGN3" (at 0 31.5 0) (effects (font (size 1.27 1.27))))',
        '    (property "Footprint" "OpenRef-FGM230SB:FGM230SB27HGN3" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))',
        '    (property "Datasheet" "https://www.silabs.com/documents/public/data-sheets/fgm230s-datasheet.pdf" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))',
        '    (symbol "FGM230SB27HGN3_0_1"',
        '      (rectangle (start -25.4 30.48) (end 25.4 -30.48) (stroke (width 0) (type default)) (fill (type background)))',
        '    )',
        '    (symbol "FGM230SB27HGN3_1_1"',
    ]
    for index, row in enumerate(rows):
        number = int(row["pin"])
        side_left = index < 24
        column = 0 if side_left else 1
        slot = index if side_left else index - 24
        x = -30.48 if side_left else 30.48
        y = 27.94 - slot * 2.54
        rotation = 0 if side_left else 180
        etype = electrical_type(row["direction"])
        shape = "line"
        body.append(
            f'      (pin {etype} {shape} (at {x:.2f} {y:.2f} {rotation}) '
            f'(length 5.08) (name "{q(row["pad"])}" (effects (font (size 1.0 1.0)))) '
            f'(number "{number}" (effects (font (size 1.0 1.0)))))'
        )
    body.extend(['    )', '  )'])
    return "\n".join(lines + body + [")", ""])


def pad_position(number: int) -> tuple[float, float, float, float]:
    if 1 <= number <= 11:
        return (-2.90, 2.50 - (number - 1) * 0.50, 0.35, 0.25)
    if 12 <= number <= 22:
        return (-2.50 + (number - 12) * 0.50, -2.90, 0.25, 0.35)
    if 23 <= number <= 33:
        return (2.90, -2.50 + (number - 23) * 0.50, 0.35, 0.25)
    if 34 <= number <= 44:
        return (2.50 - (number - 34) * 0.50, 2.90, 0.25, 0.35)
    return {
        45: (-0.45, 0.45, 0.50, 0.50),
        46: (-0.45, -0.45, 0.50, 0.50),
        47: (0.45, -0.45, 0.50, 0.50),
        48: (0.45, 0.45, 0.50, 0.50),
    }[number]


def generate_footprint() -> str:
    lines = [
        '(footprint "FGM230SB27HGN3"',
        '  (version 20240108)',
        '  (generator "openref")',
        '  (layer "F.Cu")',
        '  (descr "Silicon Labs FGM230SB 48-pad 6.5 mm SiP; datasheet rev 1.2 Figure 8.4")',
        '  (tags "FGM230SB SiP 48 pad")',
        '  (attr smd)',
        '  (fp_rect (start -3.25 -3.25) (end 3.25 3.25) (stroke (width 0.10) (type default)) (fill none) (layer "F.Fab"))',
        '  (fp_line (start -3.40 -3.40) (end -2.65 -3.40) (stroke (width 0.15) (type default)) (layer "F.SilkS"))',
        '  (fp_line (start -3.40 -3.40) (end -3.40 -2.65) (stroke (width 0.15) (type default)) (layer "F.SilkS"))',
        '  (fp_circle (center -3.55 -2.90) (end -3.45 -2.90) (stroke (width 0.10) (type default)) (fill solid) (layer "F.SilkS"))',
        '  (fp_rect (start -3.55 -3.55) (end 3.55 3.55) (stroke (width 0.05) (type default)) (fill none) (layer "F.CrtYd"))',
        '  (fp_text reference "REF**" (at 0 -4.25 0) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))',
        '  (fp_text value "FGM230SB27HGN3" (at 0 4.25 0) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))',
    ]
    for number in range(1, 49):
        x, y, sx, sy = pad_position(number)
        lines.append(
            f'  (pad "{number}" smd rect (at {x:.2f} {y:.2f}) '
            f'(size {sx:.2f} {sy:.2f}) (layers "F.Cu" "F.Mask"))'
        )
        paste_scale = math.sqrt(0.80)
        lines.append(
            f'  (pad "" smd rect (at {x:.2f} {y:.2f}) '
            f'(size {sx * paste_scale:.4f} {sy * paste_scale:.4f}) '
            '(layers "F.Paste"))'
        )
    lines.extend([')', ''])
    return "\n".join(lines)


def main() -> None:
    with CSV.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    if [int(row["pin"]) for row in rows] != list(range(1, 49)):
        raise SystemExit("controlled pin table must contain pins 1 through 48 in order")
    SYMBOL.write_text(generate_symbol(rows), encoding="utf-8", newline="\n")
    FOOTPRINT.parent.mkdir(parents=True, exist_ok=True)
    FOOTPRINT.write_text(generate_footprint(), encoding="utf-8", newline="\n")
    print(SYMBOL.relative_to(ROOT))
    print(FOOTPRINT.relative_to(ROOT))


if __name__ == "__main__":
    main()
