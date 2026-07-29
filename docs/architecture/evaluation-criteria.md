# Architecture Evaluation Criteria

**Document ID:** OR-ARC-001  
**Revision:** 0.1  
**Status:** Draft

## Purpose

Define a repeatable method for comparing architecture alternatives before selecting technologies or components.

## Mandatory Gates

An alternative is ineligible if it:

- requires internet, cloud service, subscription, or a connected phone for core communication;
- cannot support at least six simultaneous full-duplex users;
- prevents automatic recovery from common communication interruptions;
- makes the primary battery non-user-replaceable;
- creates an unacceptable safety, privacy, or regulatory risk;
- cannot reasonably be manufactured and serviced.

## Weighted Criteria

| Criterion | Weight | Evaluation Question |
|---|---:|---|
| Reliability and graceful degradation | 20 | Does the architecture protect communication and recover predictably? |
| RF robustness and coexistence | 14 | Can it operate around nearby crews and common venue RF traffic? |
| Usability and cognitive burden | 12 | Does it minimize setup, controls, and ambiguous states? |
| Communication quality and latency | 12 | Can it support natural, intelligible conversation? |
| Power efficiency | 9 | Can it meet match-day endurance without excessive size or weight? |
| Safety and security | 8 | Does it protect users, batteries, firmware, and crew privacy? |
| Serviceability | 7 | Can likely failures and wear items be diagnosed and repaired? |
| Manufacturability and testability | 6 | Can units be built, calibrated, and acceptance-tested consistently? |
| Regulatory path | 5 | Is U.S. authorization achievable without unusual operational constraints? |
| Lifecycle and supply resilience | 4 | Are critical technologies supportable over the product life? |
| Cost | 3 | Is the architecture compatible with a credible professional-product cost? |

## Scoring

Score each criterion from 0 to 5:

- 0: infeasible or unknown with critical risk
- 1: poor
- 2: weak
- 3: acceptable
- 4: strong
- 5: excellent

Weighted scores support decisions but do not override mandatory gates or engineering judgment.

## Evidence Levels

- E0: assumption
- E1: supplier or standards documentation
- E2: analytical model
- E3: bench evidence
- E4: integrated prototype evidence
- E5: representative field evidence

Architecture decisions shall identify the evidence level supporting each material score.
