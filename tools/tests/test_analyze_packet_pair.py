from pathlib import Path
import sys


sys.path.insert(0, str(Path(__file__).parents[1]))

from analyze_packet_pair import analyze


def test_analyze_packet_pair_log() -> None:
    log = Path(__file__).parent / "fixtures" / "packet-pair-sample.csv"
    summary = analyze(log)

    assert summary["received_packets"] == 3
    assert summary["first_sequence"] == 1
    assert summary["last_sequence"] == 5
    assert summary["sequence_gaps"] == 2
    assert summary["rx_gap_events"] == 1
    assert summary["boot_events"] == 1
    assert summary["inter_arrival_min_us"] == 1000
    assert summary["inter_arrival_max_us"] == 3000
    assert summary["rssi_min_dbm"] == -47
    assert summary["lqi_min"] == 218


def test_analyze_packet_pair_passes_explicit_criteria() -> None:
    log = Path(__file__).parent / "fixtures" / "packet-pair-sample.csv"
    summary = analyze(
        log,
        min_received=3,
        expected_first_sequence=1,
        expected_last_sequence=5,
        max_sequence_gaps=2,
        max_rx_gap_events=1,
        max_fault_events=0,
        max_boot_events=1,
        max_inter_arrival_us=3000,
    )

    assert summary["pass"] is True
    assert summary["failures"] == []


def test_analyze_packet_pair_fails_explicit_criteria() -> None:
    log = Path(__file__).parent / "fixtures" / "packet-pair-sample.csv"
    summary = analyze(
        log,
        min_received=4,
        max_sequence_gaps=0,
        max_rx_gap_events=0,
        max_boot_events=0,
    )

    assert summary["pass"] is False
    assert "received_packets 3 < min_received 4" in summary["failures"]
    assert "sequence_gaps 2 > max_sequence_gaps 0" in summary["failures"]
    assert "rx_gap_events 1 > max_rx_gap_events 0" in summary["failures"]
    assert "boot_events 1 > max_boot_events 0" in summary["failures"]
