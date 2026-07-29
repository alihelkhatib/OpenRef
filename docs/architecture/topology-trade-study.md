# Communication Topology Trade Study

**Document ID:** OR-ARC-007  
**Revision:** 0.1  
**Status:** Preliminary

## Alternatives Evaluated

1. Fixed central hub
2. Wearable leader star
3. Coordinated distributed system
4. Peer mesh
5. Smartphone-mediated system

The smartphone-mediated alternative fails the core offline and no-phone product gate and is excluded.

## Preliminary Scores

Scores use the 0–5 architecture scale defined in `evaluation-criteria.md`.

| Criterion | Weight | Fixed Hub | Wearable Leader | Coordinated Distributed | Peer Mesh |
|---|---:|---:|---:|---:|---:|
| Reliability and graceful degradation | 20 | 2 | 2 | 4 | 3 |
| RF robustness and coexistence | 14 | 3 | 3 | 4 | 3 |
| Usability and cognitive burden | 12 | 3 | 4 | 4 | 3 |
| Communication quality and latency | 12 | 4 | 4 | 4 | 3 |
| Power efficiency | 9 | 4 | 3 | 4 | 2 |
| Safety and security | 8 | 4 | 4 | 4 | 3 |
| Serviceability | 7 | 3 | 4 | 4 | 3 |
| Manufacturability and testability | 6 | 3 | 4 | 3 | 2 |
| Regulatory path | 5 | 4 | 4 | 4 | 3 |
| Lifecycle and supply resilience | 4 | 3 | 4 | 4 | 3 |
| Cost | 3 | 2 | 4 | 4 | 3 |

## Preliminary Conclusion

The coordinated distributed system remains the preferred direction.

The likely conceptual form is:

- no dedicated external hub;
- one wearable temporarily coordinates timing, admission, or shared resources;
- coordinator role is not permanently tied to a specific official;
- coordinator failure triggers deterministic re-election;
- audio transport avoids routing voice through multiple body-worn relay hops;
- crew identity and keys persist independently of the current coordinator.

## Rejected Direction

A general multi-hop voice mesh is not preferred for Version 1 because it introduces:

- variable path latency;
- routing instability;
- greater radio duty cycle;
- difficult fault isolation;
- harder coexistence verification;
- larger firmware scope.

Multi-hop transport may be reconsidered only if direct wearable-to-wearable coverage proves insufficient.

## Open Evidence Items

- whether physical-layer broadcast or multicast can be used efficiently;
- whether a selected radio supports deterministic scheduled access;
- coordinator election time;
- voice codec and packetization behavior;
- feasibility of simultaneous six-source reception;
- coexistence with Wi-Fi, Bluetooth, and nearby OpenRef crews;
- battery impact of continuous receive operation.
