from validate_fg23_watchdog_reset import validate_capture


def test_accepts_injected_hang_followed_by_wdog0_reset() -> None:
    text = "\n".join(
        (
            "{{(openrefReset)}{Raw:0x00000001}{Classified:0x00000001}{Watchdog:0}}}",
            "{{(openrefWatchdog)}{Status:InjectedHang}{Feeds:3}}}",
            "{{(openrefReset)}{Raw:0x00000008}{Classified:0x00000008}{Watchdog:1}}}",
        )
    )
    assert validate_capture(text, expected_feeds=3) == []


def test_rejects_reset_before_hang_or_inconsistent_classification() -> None:
    before = "\n".join(
        (
            "{{(openrefReset)}{Raw:0x00000008}{Classified:0x00000008}{Watchdog:1}}}",
            "{{(openrefWatchdog)}{Status:InjectedHang}{Feeds:2}}}",
        )
    )
    assert any("does not follow" in error for error in validate_capture(before))

    inconsistent = "\n".join(
        (
            "{{(openrefWatchdog)}{Status:InjectedHang}{Feeds:2}}}",
            "{{(openrefReset)}{Raw:0x00000008}{Classified:0x00000000}{Watchdog:1}}}",
        )
    )
    assert any("consistent" in error for error in validate_capture(inconsistent))
