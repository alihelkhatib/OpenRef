import subprocess
import sys
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "railtest_smoke.py"


def test_railtest_smoke_help() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--help"],
        capture_output=True,
        text=True,
        check=True,
    )

    assert "Run an FG23 RAILtest serial smoke test" in result.stdout


def test_railtest_marker_validation() -> None:
    sys.path.insert(0, str(SCRIPT.parents[0]))
    from railtest_smoke import railtest_output_ok

    assert railtest_output_ok(
        "\n".join(
            [
                "____Application_Configuration____",
                "____Receive_and_Transmit____",
                "getVersion",
            ]
        )
    )
    assert not railtest_output_ok(">")


def test_com_ports_sort_naturally() -> None:
    sys.path.insert(0, str(SCRIPT.parents[0]))
    from railtest_smoke import port_sort_key

    assert sorted(["COM10", "COM8"], key=port_sort_key) == ["COM8", "COM10"]
