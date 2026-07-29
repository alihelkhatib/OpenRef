from pathlib import Path

from openref_sim.run import run_scenario
from openref_sim.scenario import load_scenario


SCENARIOS = Path(__file__).parents[1] / "scenarios"


def test_nominal_six_node_schedule_has_no_collisions() -> None:
    scenario = load_scenario(SCENARIOS / "six_nodes_nominal.yaml")
    _, summary = run_scenario(scenario)
    assert summary["generated"] > 0
    assert summary["collided"] == 0
    assert summary["delivery_ratio"] == 1.0


def test_tight_slots_produce_collisions() -> None:
    scenario = load_scenario(SCENARIOS / "six_nodes_collision.yaml")
    _, summary = run_scenario(scenario)
    assert summary["collided"] > 0
    assert summary["delivery_ratio"] < 1.0
