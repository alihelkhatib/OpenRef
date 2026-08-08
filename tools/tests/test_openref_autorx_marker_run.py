from __future__ import annotations

from openref_autorx_marker_run import parse_autorx_markers


def test_parse_autorx_markers() -> None:
    text = "{{(openrefAutoRx)}{Rx:25}{Sequence:100}{Gaps:0}{Faults:0}{Gap:0}{Expected:0}}"

    assert parse_autorx_markers(text) == [
        {"rx": 25, "sequence": 100, "gaps": 0, "faults": 0}
    ]
