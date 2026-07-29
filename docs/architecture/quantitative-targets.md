# Quantitative Architecture Targets

**Document ID:** OR-ARC-005  
**Revision:** 0.1  
**Status:** Draft targets pending prototype evidence

## Purpose

Establish measurable engineering targets for architecture comparison, subsystem allocation, and prototype verification.

These values are design targets, not release claims.

## Communication

| Attribute | Target | Notes |
|---|---:|---|
| Supported active crew members | 6 minimum | Full-duplex crew conversation |
| Stretch crew size | 8 | Architecture should avoid preventing later support |
| One-way audio latency | ≤ 120 ms target | Measured microphone input to remote earpiece output |
| Maximum acceptable one-way latency | 180 ms | Beyond this requires explicit review |
| Crew formation time | ≤ 30 s | From powered units to confirmed crew readiness |
| Rejoin after transient link loss | ≤ 5 s | Without user action when credentials remain valid |
| Coordinator failover, if applicable | ≤ 3 s | Temporary audio disruption allowed but must be indicated |
| Nearby independent crews | 4 minimum | Within the same venue area without cross-association |
| Useful outdoor range | 150 m target | Body-worn units, unobstructed field conditions |
| Degraded but recoverable range | 250 m objective | Not a guaranteed release requirement |
| Packet-loss concealment interval | ≥ 40 ms | Exact method architecture-dependent |

## Audio

| Attribute | Target |
|---|---:|
| Speech bandwidth | At least 300 Hz–7 kHz |
| Microphone overload recovery | ≤ 250 ms |
| User volume steps | At least 8 usable steps |
| Wind-noise operating target | Intelligible at 25 km/h apparent wind |
| Crowd-noise validation target | Intelligible with 85 dBA representative background |
| Maximum continuous listening level | To be validated against approved headset and exposure model |
| Acoustic echo or feedback | No sustained oscillation in approved configurations |

## Power

| Attribute | Target |
|---|---:|
| Active communication endurance | 8 h minimum |
| Product objective | 10 h |
| Low-battery warning lead time | ≥ 45 min under representative load |
| Critical-battery warning lead time | ≥ 10 min |
| Replace-battery-and-recover time | ≤ 60 s |
| Shelf power-off retention | ≥ 6 months before recharge recommendation |
| Battery cycle objective | ≥ 500 cycles to 80% nominal capacity |

## Mechanical and Environmental

| Attribute | Target |
|---|---:|
| Wearable mass excluding headset | ≤ 180 g |
| Preferred wearable mass | ≤ 140 g |
| Single-drop survival | 1.5 m to representative hard surface |
| Repeated drop campaign | 10 drops from 1.0 m |
| Operating temperature | -10 °C to 45 °C target |
| Storage temperature | -20 °C to 60 °C target |
| Ingress objective | IP55 minimum design objective |
| Battery retention load | ≥ 5× wearable weight in worst direction |
| Control life | ≥ 100,000 actuations for primary controls |
| Connector mating life | ≥ 5,000 cycles for field-replaceable headset connector |

## Service and Lifecycle

| Attribute | Target |
|---|---:|
| Battery replacement | Tool-free |
| Headset replacement | Field replaceable |
| Fault-domain identification | Power, battery, radio, audio input, audio output, firmware, accessory |
| Firmware recovery | No specialized factory equipment for standard recovery |
| Production acceptance duration | ≤ 5 min per wearable target |
| Service documentation availability | Public at commercial release |

## Target Maturity

Each target shall be labeled during reviews as:

- assumed;
- analytically supported;
- bench demonstrated;
- integrated demonstrated;
- field validated;
- release verified.
