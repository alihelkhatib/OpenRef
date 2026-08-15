import copy
import json
from pathlib import Path

from validate_wearable_mechanical_contract import validate_contract


ROOT = Path(__file__).parents[2]
CONTRACT = ROOT / "hardware/prototype1-wearable/wearable-mechanical-contract.json"


def contract() -> dict:
    return json.loads(CONTRACT.read_text(encoding="utf-8"))


def test_controlled_incomplete_contract_is_valid_and_reports_real_inputs() -> None:
    errors, blockers = validate_contract(contract())
    assert errors == []
    assert "product_configuration.wear_location" in blockers
    assert "placement_decisions.antenna_location" in blockers
    assert len(blockers) == 13


def test_safety_constraint_and_antenna_battery_overlap_are_rejected() -> None:
    data = copy.deepcopy(contract())
    data["safety_constraints"]["battery_cannot_become_projectile"] = False
    next(zone for zone in data["zones"] if zone["id"] == "ANTENNA")["excludes"].remove("BATTERY")
    errors, _ = validate_contract(data)
    assert any("safety constraints" in error for error in errors)
    assert any("antenna and battery" in error for error in errors)


def test_invalid_dimensions_and_missing_verification_are_rejected() -> None:
    data = copy.deepcopy(contract())
    data["product_configuration"]["maximum_envelope_mm"]["x"] = -1
    data["required_verification"] = data["required_verification"][:-1]
    errors, _ = validate_contract(data)
    assert any("maximum_envelope_mm.x" in error for error in errors)
    assert any("required verification" in error for error in errors)
