# ADR-0001: Overall Communication Topology

**Status:** Proposed — evidence gathering  
**Decision Owner:** Systems Engineering

## Context

OpenRef must support at least six officials in natural full-duplex conversation while preserving reliability, privacy, battery endurance, and graceful degradation.

## Alternatives

### A. Centralized Star

Each wearable communicates through a designated hub or leader.

Advantages:

- simpler coordination and mixing;
- potentially predictable timing;
- centralized admission and security.

Risks:

- hub becomes a critical dependency;
- leader battery or RF position may affect the whole crew;
- failover complexity.

### B. Fully Distributed Mesh

Wearables coordinate and transport audio without a permanent central node.

Advantages:

- no fixed hub;
- potential path diversity;
- graceful membership changes.

Risks:

- timing, routing, mixing, and airtime complexity;
- higher power and firmware burden;
- harder deterministic verification.

### C. Coordinated Distributed System

A temporary coordinator manages timing or membership, but communication can recover through deterministic coordinator re-election or predefined fallback.

Advantages:

- balances coordination with recoverability;
- avoids dedicated external hub;
- can isolate complexity behind a stable state model.

Risks:

- election and transition behavior require rigorous design;
- recovery may briefly interrupt audio;
- implementation remains more complex than a fixed star.

## Preliminary Direction

Alternative C is the leading architectural hypothesis. It is not yet selected.

## Evidence Required Before Decision

- airtime and capacity analysis for six simultaneous talkers;
- end-to-end latency model;
- coordinator-loss recovery analysis;
- power comparison;
- coexistence analysis;
- security and crew-formation analysis;
- bench proof using candidate radio classes.

## Decision Gate

The ADR may be accepted only after candidate voice transport approaches and radio classes are evaluated using `evaluation-criteria.md`.
