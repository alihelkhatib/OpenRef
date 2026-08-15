import copy
import json
from pathlib import Path

from validate_fgm230_sdk_routes import validate_routes


ROOT = Path(__file__).parents[2]
ALLOCATION = ROOT / "hardware/prototype1-wearable/fgm230sb-pin-allocation.json"
DEVICE = """
#define GPIO_PA_INDEX 0U
#define GPIO_PB_INDEX 1U
#define GPIO_PC_INDEX 2U
#define GPIO_PD_INDEX 3U
#define GPIO_PA_MASK (0x07FFUL)
#define GPIO_PB_MASK (0x007FUL)
#define GPIO_PC_MASK (0x03FFUL)
#define GPIO_PD_MASK (0x003FUL)
#define GPIO_SWCLK_PORT GPIO_PA_INDEX
#define GPIO_SWCLK_PIN 1U
#define GPIO_SWDIO_PORT GPIO_PA_INDEX
#define GPIO_SWDIO_PIN 2U
#define GPIO_SWV_PORT GPIO_PA_INDEX
#define GPIO_SWV_PIN 3U
#define LFXO_LFXTAL_I_PORT GPIO_PD_INDEX
#define LFXO_LFXTAL_I_PIN 1U
#define LFXO_LFXTAL_O_PORT GPIO_PD_INDEX
#define LFXO_LFXTAL_O_PIN 0U
#define USART_COUNT 1
#define EUSART_COUNT 3
#define IADC_COUNT 1
"""
GPIO = "CSROUTE RXROUTE CLKROUTE TXROUTE"
IADC = "iadcPosInputPortAPin0"


def allocation() -> dict:
    return json.loads(ALLOCATION.read_text(encoding="utf-8"))


def test_controlled_routes_match_sdk_metadata() -> None:
    assert validate_routes(allocation(), DEVICE, GPIO, IADC) == []


def test_route_collision_and_sdk_pin_change_are_rejected() -> None:
    data = copy.deepcopy(allocation())
    data["peripheral_routes"][0]["pad"] = "PC09"
    errors = validate_routes(data, DEVICE.replace("GPIO_SWV_PIN 3U", "GPIO_SWV_PIN 4U"), GPIO, IADC)
    assert any("controlled route set" in error for error in errors)
    assert any("SWV" in error for error in errors)


def test_missing_flexible_route_and_adc_support_are_rejected() -> None:
    sdk_without_lfxo_pin = DEVICE.replace("#define LFXO_LFXTAL_I_PIN 1U\n", "")
    errors = validate_routes(allocation(), sdk_without_lfxo_pin, "CSROUTE RXROUTE", "")
    assert any("CLKROUTE" in error for error in errors)
    assert any("PA00" in error for error in errors)
    assert any("LFXTAL_I" in error for error in errors)
