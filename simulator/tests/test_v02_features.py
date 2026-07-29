from pathlib import Path

from openref_sim.run import run_scenario
from openref_sim.scenario import load_scenario

SCENARIOS = Path(__file__).parents[1] / "scenarios"


def test_burst_loss_is_recorded() -> None:
    _, summary = run_scenario(load_scenario(SCENARIOS / "packet_loss_burst.yaml"))
    assert summary["randomly_lost"] > 0
    assert 0 < summary["delivery_ratio"] < 1


def test_coordinator_failure_elects_replacement() -> None:
    sim, summary = run_scenario(load_scenario(SCENARIOS / "coordinator_failure.yaml"))
    assert summary["coordinator_changes"] >= 1
    selected = [e for e in sim.trace if e.event == "coordinator_selected"]
    assert any(e.node_id == 2 for e in selected)
    assert summary["coordinator_recovery_time_us"] == 50_000


def test_drift_scenario_is_deterministic() -> None:
    scenario = load_scenario(SCENARIOS / "six_nodes_drift.yaml")
    _, first = run_scenario(scenario)
    _, second = run_scenario(scenario)
    assert first == second
