from openref_sim.engine import Simulation


def test_events_run_in_time_then_insertion_order() -> None:
    sim = Simulation()
    observed: list[str] = []
    sim.schedule_at(10, lambda: observed.append("a"))
    sim.schedule_at(5, lambda: observed.append("b"))
    sim.schedule_at(10, lambda: observed.append("c"))
    sim.run(10)
    assert observed == ["b", "a", "c"]
