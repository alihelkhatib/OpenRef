import csv
from pathlib import Path

from export_fgm230_symbol_pins import export_pins


ROOT = Path(__file__).parents[2]
SOURCE = ROOT / "hardware/prototype1-wearable/fgm230sb-pin-allocation.json"
TRACKED = ROOT / "hardware/prototype1-wearable/cad/fgm230sb-symbol-pins.csv"


def test_tracked_symbol_table_is_reproducible(tmp_path: Path) -> None:
    generated = tmp_path / "pins.csv"
    export_pins(SOURCE, generated)
    assert generated.read_bytes() == TRACKED.read_bytes()
    with generated.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 48
    assert rows[12]["pad"] == "PA01" and rows[12]["net"] == "RADIO_SWCLK"
    assert rows[17]["direction"] == "no_connect"
    assert rows[23]["direction"] == "no_connect"
