import copy
import json
from pathlib import Path

from validate_prototype1_connectivity import validate_connectivity


ROOT = Path(__file__).parents[2]


def load(name: str) -> dict:
    return json.loads((ROOT / "hardware/prototype1-wearable" / name).read_text(encoding="utf-8"))


def inputs() -> tuple[dict, dict, dict]:
    return load("schematic-connectivity.json"), load("electrical-interface-contract.json"), load("fgm230sb-pin-allocation.json")


def test_controlled_connectivity_is_consistent() -> None:
    assert validate_connectivity(*inputs()) == []


def test_missing_isolation_and_current_measurement_are_rejected() -> None:
    graph, contract, allocation = inputs()
    graph = copy.deepcopy(graph)
    next(path for path in graph["signal_paths"] if path["net"] == "AUD_CIPO")["via"] = []
    next(path for path in graph["power_paths"] if path["net"] == "V_AUDIO")["current_link"] = False
    errors = validate_connectivity(graph, contract, allocation)
    assert any("AUD_CIPO requires LINK_ISOLATION" in error for error in errors)
    assert any("V_AUDIO requires a current link" in error for error in errors)


def test_unsafe_audio_and_rf_bypass_are_rejected() -> None:
    graph, contract, allocation = inputs()
    graph = copy.deepcopy(graph)
    next(path for path in graph["signal_paths"] if path["net"] == "EARPIECE_AUDIO")["via"] = []
    next(path for path in graph["signal_paths"] if path["net"] == "RF_50OHM")["via"] = []
    errors = validate_connectivity(graph, contract, allocation)
    assert any("EARPIECE_AUDIO" in error for error in errors)
    assert any("RF_50OHM" in error for error in errors)
