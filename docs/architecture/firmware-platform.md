# Firmware Platform Architecture

**Document ID:** OR-ARC-012  
**Revision:** 0.1  
**Status:** Baseline decomposition

## Execution Domains

The firmware shall be decomposed into bounded execution domains:

1. Boot and recovery
2. Hardware abstraction
3. Radio driver
4. Network timing and membership
5. Security services
6. Audio capture and playback
7. Codec and packet-loss handling
8. Mixer
9. Power and battery management
10. User controls and status
11. Persistent configuration
12. Diagnostics and production test
13. Firmware update

## Priority Order

Highest to lowest:

1. audio sample deadlines;
2. radio timing deadlines;
3. network recovery and security validation;
4. power safety;
5. user controls and indications;
6. persistent writes;
7. diagnostics and logging;
8. maintenance functions.

## Concurrency Rules

- no noncritical task may block audio or radio deadlines;
- inter-domain communication shall use bounded queues;
- every queue shall have an explicit overflow policy;
- watchdog coverage shall include deadline monitoring, not only task liveness;
- interrupt service routines shall remain minimal;
- persistent storage access shall be asynchronous to critical paths.

## Fault Containment

Each domain shall define:

- detected fault conditions;
- maximum recovery time;
- reset scope;
- user-visible indication;
- retained diagnostic evidence.

A recoverable audio-path fault should not require erasing crew credentials or factory configuration.

## Memory Discipline

- static allocation for communication-critical paths;
- versioned persistent records;
- dual-copy or transactional storage for critical configuration;
- bounded log storage;
- stack high-water monitoring during development;
- compile-time size checks for protocol structures.
