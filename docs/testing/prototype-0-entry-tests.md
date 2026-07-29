# Prototype 0 Entry Tests

**Document ID:** OR-TST-004  
**Revision:** 0.1  
**Status:** Ready for initial boards

## Purpose

Define the tests that must pass before implementing the complete six-node voice protocol.

## E0-01 Toolchain Reproduction

A clean development machine shall:

- build the selected vendor example;
- program a board;
- capture serial output;
- reproduce the process from repository instructions.

## E0-02 Continuous Packet Pair

Two boards shall exchange timestamped packets continuously for one hour.

Record:

- sent packets;
- received packets;
- CRC failures;
- sequence gaps;
- reset count;
- minimum, mean, p95, p99, and maximum inter-arrival time.

## E0-03 Scheduled Transmission

One board shall schedule repeated transmissions relative to its radio clock.

Measure actual launch variation using a GPIO marker.

## E0-04 Payload Capacity Sweep

For each candidate radio profile, sweep payload size and interval until:

- deadline failures occur;
- receive loss becomes unacceptable;
- queues overflow;
- or planned channel utilization reaches its limit.

## E0-05 Controlled Attenuation

Introduce increasing RF attenuation while recording:

- RSSI;
- packet delivery;
- burst losses;
- recovery time;
- latency.

## E0-06 Radio Fault Recovery

Inject:

- transmit cancellation;
- receive cancellation;
- malformed packet;
- queue saturation;
- forced radio reset.

The application shall return to a defined state without unbounded memory growth.

## E0-07 Audio Loopback Timing

Generate a known audio impulse or digital marker.

Measure:

- capture frame creation;
- packet queue;
- radio transmission;
- reception;
- playback output.

This establishes the measurement method before the codec and six-node mixer are introduced.

## Exit Criteria

Proceed to the six-node network protocol only when all entry tests have reproducible scripts, stored raw results, and no unexplained resets.
