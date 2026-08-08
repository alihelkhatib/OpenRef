from pathlib import Path

from openref_sim.capacity import estimate_capacity
from openref_sim.scenario import load_scenario


SCENARIOS = Path(__file__).parents[1] / "scenarios"


def test_nominal_capacity_estimate_matches_airtime_model() -> None:
    scenario = load_scenario(SCENARIOS / "six_nodes_nominal.yaml")
    estimate = estimate_capacity(scenario)

    assert estimate.voice_airtime_us == 1316
    assert estimate.heartbeat_airtime_us == 484
    assert estimate.slot_guard_us == 1184
    assert estimate.schedule_span_us == 13_816
    assert round(estimate.scheduled_channel_utilization, 4) == 0.3996
