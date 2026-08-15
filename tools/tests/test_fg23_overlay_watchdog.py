from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "install_openref_fg23_overlay.ps1"


def test_overlay_installs_and_can_enable_fg23_watchdog() -> None:
    text = SCRIPT.read_text(encoding="utf-8")
    assert text.count("[switch]$EnableHardwareWatchdog") == 1
    assert text.count("OPENREF_APP_WATCHDOG_FG23=1") == 1
    assert text.count("OPENREF_APP_RESET_CAUSE_FG23=1") == 1
    assert "[uint32]$WatchdogTestHangAfterFeeds = 0" in text
    assert "OPENREF_APP_WATCHDOG_TEST_HANG_AFTER_FEEDS=$WatchdogTestHangAfterFeeds" in text
    assert 'throw "-WatchdogTestHangAfterFeeds requires -EnableHardwareWatchdog."' in text
    assert '[string]$WatchdogHangMarker = ""' in text
    assert '[string]$WatchdogBootMarker = ""' in text
    assert 'throw "Watchdog markers require -EnableHardwareWatchdog."' in text
    assert '-Label "WATCHDOG_HANG"' in text
    assert '-Label "WATCHDOG_BOOT"' in text
    for filename in (
        "openref_watchdog_gate.h",
        "openref_watchdog_gate.c",
        "openref_watchdog_driver.h",
        "openref_watchdog_driver.c",
        "openref_watchdog_fg23.h",
        "openref_watchdog_fg23.c",
        "openref_reset_cause_fg23.h",
        "openref_reset_cause_fg23.c",
    ):
        assert filename in text
