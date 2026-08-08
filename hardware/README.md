# OpenRef Hardware

Hardware work is staged to avoid designing a custom wearable PCB before the
radio, power, and audio assumptions have measured support.

## Current Hardware Tracks

| Track | Status | Purpose |
|---|---|---|
| `prototype0-support/` | Can start now | Bench fixtures and support PCBs for dev-board testing. |
| `prototype1-wearable/` | Planning only | Future custom wearable electronics after Prototype 0 evidence. |

## PCB Rule

Prototype 0 support PCBs may be designed before the FG23 boards arrive if they
only provide measurement, audio-load, connector-breakout, or wiring support.

Do not start the custom RF/wearable PCB layout until Prototype 0 has measured:

- radio packet timing;
- scheduled TX launch error;
- current draw by operating mode;
- antenna/body-placement constraints;
- audio input/output architecture;
- battery voltage and charging assumptions.
