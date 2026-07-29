from openref_sim.packet import packet_airtime_us


def test_airtime_rounds_up() -> None:
    assert packet_airtime_us(60, 500_000, 16, 100) == 1316
