import copy
import json
from pathlib import Path

from validate_fgm230_pin_allocation import validate_allocation


ROOT = Path(__file__).parents[2]
ALLOCATION = ROOT / "hardware/prototype1-wearable/fgm230sb-pin-allocation.json"


def allocation() -> dict:
    return json.loads(ALLOCATION.read_text(encoding="utf-8"))


def test_controlled_allocation_is_valid() -> None:
    assert validate_allocation(allocation()) == []


def test_debug_collision_and_missing_pin_are_rejected() -> None:
    data = allocation()
    data["pins"] = [pin for pin in data["pins"] if pin["pin"] != 48]
    next(pin for pin in data["pins"] if pin["pad"] == "PA01")["net"] = "BUTTON"
    errors = validate_allocation(data)
    assert any("1 through 48" in error for error in errors)
    assert any("PA01" in error and "RADIO_SWCLK" in error for error in errors)


def test_no_connect_and_supply_rules_are_rejected() -> None:
    data = copy.deepcopy(allocation())
    next(pin for pin in data["pins"] if pin["pad"] == "VDCDC")["net"] = "V_RADIO"
    next(pin for pin in data["pins"] if pin["pad"] == "IOVDD")["safe_state"] = "none"
    errors = validate_allocation(data)
    assert any("VDCDC" in error and "no-connect" in error for error in errors)
    assert any("IOVDD" in error and "10 uF" in error for error in errors)
