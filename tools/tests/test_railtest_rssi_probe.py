import sys
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "railtest_rssi_probe.py"
sys.path.insert(0, str(SCRIPT.parents[0]))

from railtest_rssi_probe import parse_rssi, summarize_rssi


def test_parse_rssi_decimal_value() -> None:
    assert parse_rssi("{{(getRssi)}{rssi:-112.50}}") == -112.5


def test_parse_rssi_missing_value() -> None:
    assert parse_rssi(">") is None


def test_summarize_rssi_passes_on_delta() -> None:
    summary = summarize_rssi(
        rx_port="COM8",
        tx_port="COM10",
        rf_path=0,
        baseline_rssi_dbm=-100.0,
        tone_rssi_dbm=-70.0,
        min_delta_db=10.0,
    )

    assert summary["delta_db"] == 30.0
    assert summary["tone_detected"] is True
    assert summary["pass"] is True


def test_summarize_rssi_fails_missing_reading() -> None:
    summary = summarize_rssi(
        rx_port="COM8",
        tx_port="COM10",
        rf_path=0,
        baseline_rssi_dbm=None,
        tone_rssi_dbm=-70.0,
        min_delta_db=10.0,
    )

    assert summary["delta_db"] is None
    assert summary["tone_detected"] is False
    assert summary["pass"] is False


def test_summarize_rssi_passes_expected_no_tone() -> None:
    summary = summarize_rssi(
        rx_port="COM8",
        tx_port="COM10",
        rf_path=1,
        baseline_rssi_dbm=-95.0,
        tone_rssi_dbm=-92.0,
        min_delta_db=10.0,
        expect="no-tone",
    )

    assert summary["delta_db"] == 3.0
    assert summary["tone_detected"] is False
    assert summary["pass"] is True


def test_summarize_rssi_fails_unexpected_tone() -> None:
    summary = summarize_rssi(
        rx_port="COM8",
        tx_port="COM10",
        rf_path=1,
        baseline_rssi_dbm=-95.0,
        tone_rssi_dbm=-60.0,
        min_delta_db=10.0,
        expect="no-tone",
    )

    assert summary["tone_detected"] is True
    assert summary["pass"] is False
