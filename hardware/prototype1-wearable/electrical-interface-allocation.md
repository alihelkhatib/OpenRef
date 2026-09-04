# Prototype 1 Electrical Interface Allocation

**Status:** Pre-schematic baseline

## Processor Boundary

| Signal | Direction at FG23 | Requirement |
|---|---|---|
| SPI clock | Output | 8 MHz minimum; series-resistor footprint |
| SPI controller-out/peripheral-in | Output | Fixed 98-byte transactions |
| SPI peripheral-out/controller-in | Input | Fixed 98-byte transactions |
| SPI chip select | Output | One transaction per assertion |
| Audio request | Input | Active low and interrupt capable |
| Audio reset | Output | Active low; defined during both-rail startup |
| Radio reset request | Input | Optional peer recovery request |
| Ground | Shared | Continuous return beside high-speed signals |

## Debug and Production Test

Prototype 1 exposes compact, normally unpopulated interfaces:

- SWD clock, data, reset, reference voltage, and ground for each processor;
- serial TX/RX and ground for structured logs from each processor;
- boot/recovery strap access;
- processor-link SPI and request test pads;
- radio TX-start, audio capture-ready, and playback-commit timing markers;
- removable current links for radio, audio, and codec/headset domains;
- battery voltage, temperature, regulator enable, and power-good pads.

A Tag-Connect-style footprint is the prototype debug direction, but the exact
footprint is not frozen. Production pads remain fixture-accessible after
assembly without becoming user-accessible conductors.

## Headset, Controls, and Status

Allocate microphone, microphone return, earpiece drive/return, accessory ID,
shield/drain, and connector-detect functions. Allocate direct GPIO for
power/latch, volume up, volume down, and crew/join, plus at least one multicolor
indicator and one vibration-driver control. The connector family remains a
mechanical decision.

