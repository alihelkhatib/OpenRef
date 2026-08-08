import subprocess
import sys
from pathlib import Path

from openref_scheduled_tx_run import parse_schedtx_markers, summarize_markers


SCRIPT = Path(__file__).parents[1] / "openref_scheduled_tx_run.py"


def test_scheduled_tx_help() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--help"],
        capture_output=True,
        text=True,
        check=True,
    )

    assert "OpenRef AutoRole scheduled-TX timing probe" in result.stdout


def test_parse_and_summarize_schedtx_markers() -> None:
    text = """
    {{(openrefSchedTx)}{Status:Queued}{Sequence:1}{Attempt:1}{RequestedUs:1000}{Length:78}{Written:78}{RailStatus:0}}}
    {{(openrefSchedTx)}{Status:Started}{Sequence:1}{RequestedUs:1000}{StartUs:1004}{LaunchErrorUs:4}}}
    {{(openrefSchedTx)}{Status:Done}{Sequence:1}{UserTx:1}{UserTxStarted:1}}}
    {{(openrefSchedTx)}{Status:Summary}{Attempts:1}{Accepted:1}{Rejected:0}{UserTx:1}{UserTxStarted:1}}}
    """

    markers = parse_schedtx_markers(text)
    summary = summarize_markers(markers)

    assert summary["queued"] == 1
    assert summary["started"] == 1
    assert summary["done"] == 1
    assert summary["summary_attempts"] == 1
    assert summary["launch_error_max_us"] == 4
