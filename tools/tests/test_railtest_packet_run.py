import sys
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "railtest_packet_run.py"
sys.path.insert(0, str(SCRIPT.parents[0]))

from railtest_packet_run import parse_last_event_fields


def test_parse_last_event_fields() -> None:
    text = """
{{(status)}{RxCount:0}{SyncDetect:0}}
{{(status)}{RxCount:20}{SyncDetect:20}{RxCrcErrDrop:0}}
"""
    assert parse_last_event_fields(text, "status") == {
        "RxCount": "20",
        "SyncDetect": "20",
        "RxCrcErrDrop": "0",
    }


def test_parse_last_event_fields_missing_event() -> None:
    assert parse_last_event_fields(">", "txEnd") == {}
