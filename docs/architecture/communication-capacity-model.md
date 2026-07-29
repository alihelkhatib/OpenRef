# Communication Capacity Model

**Document ID:** OR-ARC-006  
**Revision:** 0.1  
**Status:** Initial analytical model

## Purpose

Provide a technology-independent model for evaluating whether a candidate radio and voice transport can support six simultaneous full-duplex participants.

## Fundamental Load

For `N` active participants, every participant produces one uplink audio stream.

A naive all-to-all transport creates:

- `N` source streams;
- `N × (N - 1)` delivered stream copies;
- local mixing or network mixing requirements.

For six users:

- 6 source streams;
- 30 destination stream copies.

This does not imply 30 independent RF transmissions are required. Efficient architectures may use broadcast, multicast, centralized mixing, or shared scheduled transport.

## Audio Payload Model

Let:

- `R_c` = encoded voice bitrate;
- `H` = protocol and security overhead per packet;
- `T_p` = packetization interval;
- `F` = redundancy or forward-error-correction factor;
- `N` = number of simultaneous talkers.

Approximate aggregate source bitrate:

`R_source = N × (R_c + H / T_p) × F`

The actual RF channel load must additionally include:

- medium-access overhead;
- acknowledgments or retransmissions;
- timing guards;
- beaconing and membership traffic;
- coexistence margins;
- encryption metadata;
- control and recovery traffic.

## Initial Evaluation Cases

Candidate architectures shall be modeled at minimum for:

- 16 kbps voice, 20 ms packets;
- 24 kbps voice, 20 ms packets;
- 32 kbps voice, 10 ms packets;
- all six users continuously active;
- two dominant talkers with intermittent crew responses;
- temporary 10%, 20%, and 30% frame loss;
- four nearby independent crews.

## Capacity Margin

A candidate shall not be accepted based on average match speech activity alone.

For architecture selection, the modeled worst-case scheduled channel load should remain below:

- 60% preferred;
- 75% maximum without strong evidence.

The unused margin supports interference, retries, clock drift, control traffic, and implementation uncertainty.

## Mixing Alternatives

### Local Mix at Every Wearable

Each unit receives multiple remote source streams and performs local mixing.

Benefits:

- individualized sidetone and gain;
- no single network audio mixer.

Costs:

- high downlink stream count;
- higher processing and receive duty cycle;
- more complex synchronization.

### Coordinator Mix

A coordinator receives source streams, creates one or more mixes, and distributes them.

Benefits:

- lower receiver stream count;
- centralized timing and policy.

Costs:

- coordinator workload;
- failover discontinuity;
- possible single-point degradation.

### Distributed Shared-Medium Audio

Each source transmits in assigned opportunities and all members receive the common set.

Benefits:

- efficient physical broadcast;
- no duplicated per-destination RF payload.

Costs:

- strict timing;
- collision and admission complexity;
- receiver must decode multiple sources.

## Required Prototype Evidence

The capacity model shall be replaced or calibrated with measured evidence including:

- useful payload throughput;
- RF airtime utilization;
- retry behavior;
- latency distribution;
- CPU and memory load;
- receive/transmit duty cycle;
- six-user simultaneous speech;
- interference coexistence.
