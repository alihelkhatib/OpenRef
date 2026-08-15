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


def test_four_node_schedule_reserves_six_slots_without_collisions() -> None:
    scenario = load_scenario(SCENARIOS / "four_nodes_tdma.yaml")
    _, summary = run_scenario(scenario)
    assert scenario.node_count == 4
    assert scenario.schedule_slots == 6
    assert summary["collided"] == 0
    assert summary["delivery_ratio"] == 1.0
    assert summary["queue_overflows"] == 0
    assert summary["audio_deadline_misses"] == 0
    assert summary["slot_guard_us"] > 1_000
    assert summary["schedule_span_us"] < scenario.frame_interval_us


def test_six_node_lc3_wideband_load_fits_schedule_and_margin() -> None:
    scenario = load_scenario(SCENARIOS / "six_nodes_lc3_wideband.yaml")
    _, summary = run_scenario(scenario)
    assert scenario.payload_bytes == 80
    assert scenario.wire_payload_bytes == 96
    assert summary["voice_airtime_us"] == 1924
    assert summary["heartbeat_airtime_us"] == 1924
    assert summary["slot_guard_us"] == 576
    assert summary["schedule_span_us"] == 14424
    assert summary["scheduled_channel_utilization"] < 0.6
    assert summary["collided"] == 0
    assert summary["delivery_ratio"] == 1.0


def test_tight_slots_produce_collisions() -> None:
    scenario = load_scenario(SCENARIOS / "six_nodes_collision.yaml")
    _, summary = run_scenario(scenario)
    assert summary["collided"] > 0
    assert summary["delivery_ratio"] < 1.0
