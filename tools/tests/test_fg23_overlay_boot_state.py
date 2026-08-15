from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "install_openref_fg23_overlay.ps1"


def test_overlay_installs_and_can_enable_boot_state_backend() -> None:
    text = SCRIPT.read_text(encoding="utf-8")

    assert text.count("[switch]$EnablePersistentBootState") == 1
    assert text.count("OPENREF_APP_BOOT_STATE_NVM3=1") == 1
    for filename in (
        "openref_boot_policy.h",
        "openref_boot_policy.c",
        "openref_boot_state_store.h",
        "openref_boot_state_store.c",
        "openref_boot_state_store_fg23.h",
        "openref_boot_state_store_fg23.c",
    ):
        assert filename in text

    assert "../openref/common/openref_boot_policy.c" in text
    assert "../openref/common/openref_boot_state_store.c" in text
    assert "../openref/fg23/openref_boot_state_store_fg23.c" in text
