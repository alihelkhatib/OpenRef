import copy
import json
from pathlib import Path

from validate_prototype1_interface_contract import validate_contract


ROOT = Path(__file__).parents[2]
CONTRACT = ROOT / "hardware/prototype1-wearable/electrical-interface-contract.json"


def load_contract() -> dict:
    return json.loads(CONTRACT.read_text(encoding="utf-8"))


def test_controlled_contract_is_valid() -> None:
    assert validate_contract(load_contract()) == []


def test_missing_link_and_unsafe_reset_are_rejected() -> None:
    data = load_contract()
    data["signals"] = [s for s in data["signals"] if s["name"] != "AUD_CSN"]
    data["signals"][0]["reset_state"] = "unknown"
    errors = validate_contract(data)
    assert any("AUD_CSN" in error for error in errors)
    assert any("safe reset state" in error for error in errors)


def test_duplicate_domain_and_missing_test_access_are_rejected() -> None:
    data = load_contract()
    data["power_domains"].append(copy.deepcopy(data["power_domains"][0]))
    del data["signals"][0]["test_access"]
    errors = validate_contract(data)
    assert any("unique" in error for error in errors)
    assert any("test-access" in error for error in errors)
