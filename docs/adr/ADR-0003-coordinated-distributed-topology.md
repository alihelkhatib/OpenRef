# ADR-0003: Coordinated Distributed Communication Topology

**Status:** Proposed  
**Date:** 2026-07-29

## Decision

Use a coordinated distributed topology as the baseline architecture for further design and prototyping.

A wearable unit may temporarily perform coordination functions, but the crew shall not depend permanently on a dedicated hub or a specific official's unit.

## Required Properties

- deterministic crew formation;
- authenticated membership;
- stable crew identity independent of current coordinator;
- bounded coordinator election or handoff;
- automatic rejoin after transient loss;
- no required multi-hop voice routing in the baseline design;
- clear degraded-state indication;
- fault containment so one malformed unit cannot indefinitely disrupt the crew.

## Rationale

This topology best balances:

- no external hub;
- simple match setup;
- graceful recovery;
- predictable latency;
- lower power than general mesh routing;
- future support for additional members.

## Consequences

- coordinator election and timing become safety-relevant firmware functions;
- network state must be explicitly modeled;
- security credentials cannot be tied solely to one coordinator;
- prototype testing must include coordinator fault injection;
- radio selection must support the required scheduling and broadcast behavior.

## Reconsideration Triggers

Reopen this ADR if:

- six-user airtime cannot be supported with adequate margin;
- coordinator failover cannot meet the target;
- continuous receive power prevents endurance targets;
- direct field coverage is inadequate;
- regulatory constraints make the selected implementation impractical.
