# P0 Support Fixture Requirements

**Status:** Draft

## Purpose

Provide a simple bench PCB or wiring fixture that makes FG23 Prototype 0 tests
repeatable.

## Required Functions

### GPIO Timing Breakout

- expose at least 8 logic-analyzer channels;
- provide adjacent ground pins;
- label expected signals:
  - packet build;
  - TX queue;
  - TX start;
  - TX done;
  - RX start;
  - RX done;
  - fault marker;
  - spare.

### Current Measurement

- provide a safe insertion point for current measurement;
- support USB-powered dev-board testing without modifying the board;
- clearly label source, load, and measurement direction;
- avoid exposed conductors that can easily short USB power.

### Audio Test Loads

- provide resistive loads for initial audio output testing;
- provide labeled audio loopback pads or connector positions;
- keep human earphones out of the first unsafe gain tests.

### Reset and Fault Injection

- provide labeled jumper/button points for reset or fault injection where the dev
  board exposes suitable pins;
- avoid permanent modifications to the FG23 dev boards.

### Mechanical

- include mounting holes or standoff points;
- leave room for clip leads and logic-analyzer probes;
- use large labels and test points;
- prioritize one-board bench clarity over enclosure fit.

## Non-Goals

- RF antenna matching;
- final headset connector;
- battery latch or charging;
- production audio path;
- wearable form factor;
- environmental sealing.

## Open Inputs

- FG23-DK2600A accessible header/pin map;
- selected GPIO pins for timing markers;
- available current measurement equipment;
- audio breakout or codec choice;
- preferred connector style for the fixture.
