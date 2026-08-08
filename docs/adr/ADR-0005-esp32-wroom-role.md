# ADR-0005: ESP32-WROOM Role in Prototype 0

**Status:** Accepted  
**Date:** 2026-07-30  
**Revision:** 0.1

## Decision

Do not use ESP32-WROOM as the lead Prototype 0 radio platform.

Retain ESP32-class hardware as an optional secondary tool for:

- user-interface or configuration experiments;
- debug bridges;
- inexpensive audio and codec experiments;
- later 2.4 GHz comparison work;
- noncritical bench utilities.

This decision does not ban ESP32 modules from the project. It keeps the first
radio-risk prototype focused on the sub-GHz scheduled-packet architecture.

## Context

ESP32-WROOM modules are inexpensive, widely available, and familiar. They provide
strong general-purpose embedded capability and integrated 2.4 GHz Wi-Fi and
Bluetooth/BLE.

OpenRef Prototype 0 is currently trying to answer a narrower question:

Can a controlled, low-latency, six-node, body-worn voice transport be built with
deterministic packet timing, measured airtime, coordinator recovery, and usable
range?

The lead Prototype 0 path uses the Silicon Labs `FG23-DK2600A` because it gives
direct access to 868-915 MHz proprietary packet experiments, radio timing, and
sub-GHz body-worn range evidence.

## Rationale

ESP32-WROOM is not the best lead radio-risk platform because:

- it primarily targets 2.4 GHz Wi-Fi and Bluetooth/BLE rather than the current
  sub-GHz scheduled-radio experiment;
- Wi-Fi throughput is high, but latency and airtime are shaped by contention and
  coexistence behavior that the first prototype is intentionally trying to
  control;
- Bluetooth audio and BLE topologies do not naturally provide OpenRef's desired
  six-user full-duplex crew model with project-controlled recovery semantics;
- sports venues can be crowded with phones, Wi-Fi, Bluetooth accessories,
  cameras, hotspots, and scoring equipment;
- using ESP32 first would shift the experiment from "can our scheduled
  packet-voice architecture work?" to "can we make a Wi-Fi/Bluetooth system good
  enough?"

## Consequences

- The first purchased boards remain two `FG23-DK2600A` development kits.
- The firmware scaffold remains organized around an FG23 two-board entry test.
- ESP32 work should not block FG23 E0-01 through E0-03.
- If ESP32 is introduced, it should have a specific supporting role and a test
  question separate from the lead radio experiment.

## Reconsideration Triggers

Reopen this decision if:

- FG23 cannot expose the timing or metadata needed for Prototype 0;
- sub-GHz measured current, range, or airtime becomes clearly unsuitable;
- a Wi-Fi/Bluetooth architecture is deliberately selected for a new prototype
  branch;
- ESP32-class silicon is needed for a non-radio subsystem such as configuration,
  logging, or audio processing;
- measured 2.4 GHz coexistence evidence becomes stronger than the sub-GHz path.
