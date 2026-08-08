# PCB Development Plan

**Document ID:** OR-HW-003  
**Revision:** 0.1  
**Status:** Initial plan

## Purpose

Define which PCB work can begin before Prototype 0 radio evidence exists, and
which PCB work must wait for measured results.

## Can Start Now

Prototype 0 support hardware:

- audio load and loopback fixture;
- headset connector breakout;
- GPIO timing-marker breakout;
- current-measurement harness;
- power-injection and reset/fault-injection fixture;
- cable organization for two-board and six-board bench testing.

These boards do not decide the final product architecture. They make bench tests
repeatable.

## Must Wait

The custom wearable radio/audio/power PCB shall wait until Prototype 0 measures:

- actual packet airtime;
- scheduled TX timing error;
- useful throughput;
- RX/TX/idle current;
- coordinator and member current;
- antenna placement constraints;
- audio codec and microphone interface direction;
- battery voltage, charge strategy, and protection architecture.

## Recommended First PCB

Start with a **Prototype 0 support fixture PCB**.

Its job is to connect bench equipment to the dev boards safely and repeatably,
not to miniaturize the product.

Minimum useful functions:

- GPIO marker header for logic analyzer channels;
- labeled ground references;
- current-measurement insertion points;
- resistive audio loads;
- audio loopback connector pads;
- reset/fault-injection buttons or jumper points;
- mounting holes or cable strain relief.

## Custom Wearable PCB Gate

Begin custom wearable schematic only after:

1. E0-01 toolchain reproduction passes;
2. E0-02 one-hour packet pair passes;
3. E0-03 scheduled TX timing is compatible with slot guard;
4. current profile is measured for at least TX, RX, idle, and continuous packet
   modes;
5. the architecture team decides whether the first wearable board uses an SoC,
   certified module, or external transceiver.

## Output Artifacts

For each PCB, keep:

- schematic source;
- PCB layout source;
- PDF schematic export;
- fabrication notes;
- assembly notes;
- BOM with manufacturer part numbers;
- design-review checklist;
- bring-up checklist.
