import subprocess
import sys
from pathlib import Path

from openref_malformed_rx_probe import PARSE_FAIL_TEXT, malformed_packet


SCRIPT = Path(__file__).parents[1] / "openref_malformed_rx_probe.py"


def test_malformed_rx_probe_help() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--help"],
        capture_output=True,
        text=True,
        check=True,
    )

    assert "Inject malformed packets into OpenRef AutoRole RX" in result.stdout


def test_malformed_packet_has_bad_magic_and_expected_length() -> None:
    packet = malformed_packet(payload_bytes=60)

    assert len(packet) == 78
    assert packet[:2] == b"\x00\x00"


def test_parse_fail_text_matches_serial_marker() -> None:
    text = "{{(openrefAutoRx)}{Status:ParseFail}{Length:78}{Faults:1}}}"

    assert text.count(PARSE_FAIL_TEXT) == 1
