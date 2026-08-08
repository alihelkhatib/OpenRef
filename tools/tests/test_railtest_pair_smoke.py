import sys
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "railtest_pair_smoke.py"
sys.path.insert(0, str(SCRIPT.parents[0]))

from railtest_pair_smoke import output_has_packet_exchange, tx_wait_seconds


def test_packet_exchange_marker_validation() -> None:
    assert output_has_packet_exchange("{rxPacket:len:60}", "{txEnd:status:0}")
    assert output_has_packet_exchange("{rxPacket:len:60}", "{txPacket:len:60}")
    assert not output_has_packet_exchange("{rxPacket:len:60}", ">")
    assert not output_has_packet_exchange(">", "{txEnd:status:0}")


def test_tx_wait_scales_with_packet_delay() -> None:
    assert tx_wait_seconds(packets=1000, tx_delay_ms=20, settle_seconds=12) == 25
    assert tx_wait_seconds(packets=20, tx_delay_ms=20, settle_seconds=12) == 12
    assert tx_wait_seconds(packets=1000, tx_delay_ms=None, settle_seconds=12) == 12
