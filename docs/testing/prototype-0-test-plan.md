# Prototype 0 Network Test Plan

**Document ID:** OR-TST-003  
**Revision:** 0.1  
**Status:** Draft

## Objective

Demonstrate that a candidate radio, topology, codec, and processor can support the essential communication architecture before custom wearable hardware is designed.

## Prototype Scope

Prototype 0 may use development boards, wired headsets, laboratory supplies, and nonwearable antennas.

It shall include six nodes.

## Required Demonstrations

### P0-01 Crew Formation

- create one six-member crew;
- measure formation time;
- reject a seventh unauthorized or unrelated device;
- repeat at least 30 times.

### P0-02 Simultaneous Voice

- inject six independent audio sources;
- verify every node receives the required remote mix;
- measure packet loss, latency, CPU load, memory use, and airtime.

### P0-03 Coordinator Failure

- remove power from the active coordinator;
- measure interruption;
- verify stable crew identity;
- verify restored communication.

### P0-04 Rejoin

- isolate one unit;
- restore connectivity;
- verify automatic authenticated rejoin;
- measure recovery time.

### P0-05 Nearby Crews

- operate at least two independent six-node crews simultaneously;
- verify no cross-association;
- measure interference and capacity impact.

### P0-06 Congestion

Introduce representative co-channel and adjacent-channel traffic.

Measure:

- one-way latency percentile distribution;
- packet loss;
- audible artifacts;
- recovery behavior;
- channel utilization.

### P0-07 Power

Measure current for:

- coordinator idle;
- coordinator worst-case;
- member idle;
- member worst-case;
- poor-link condition.

## Exit Criteria

Prototype 0 passes when:

- six-user communication is sustained;
- latency remains within the architecture limit;
- coordinator loss recovers automatically;
- crew isolation remains intact;
- projected endurance is feasible;
- no unbounded queue, memory, or processor behavior occurs.
