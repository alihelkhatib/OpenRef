from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "install_openref_fg23_overlay.ps1"


def test_overlay_installs_and_can_enable_device_record_backend() -> None:
    text = SCRIPT.read_text(encoding="utf-8")
    assert text.count("[switch]$EnablePersistentDeviceRecord") == 1
    assert text.count("OPENREF_APP_DEVICE_RECORD_NVM3=1") == 1
    for filename in (
        "openref_device_lifecycle.h",
        "openref_device_lifecycle.c",
        "openref_device_record_store.h",
        "openref_device_record_store.c",
        "openref_device_record_store_fg23.h",
        "openref_device_record_store_fg23.c",
    ):
        assert filename in text
