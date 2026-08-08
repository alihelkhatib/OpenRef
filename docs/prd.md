# OpenRef Product Requirements Document

**Status:** Working draft
**Source documents:** Requirements register, SRS, product philosophy, and
program roadmap

## Product Summary

OpenRef is a body-worn communication system for sports match officials. Version
1 is scoped to U.S. operation and targets rugby and soccer crews that need
continuous, low-latency voice communication without phones, internet service,
cellular service, cloud services, subscriptions, or venue infrastructure.

## Primary Users

- Center referees and assistant referees.
- Match officials working as a crew before, during, and after match play.
- Club, school, tournament, and community-sport organizations that need
  repeatable setup and maintainable equipment.

## Core Needs

- Six authorized officials can communicate at the same time.
- Any official can speak without requesting a turn.
- Crew setup is simple, repeatable, and confirms readiness clearly.
- Nearby crews remain isolated from one another.
- Temporary radio disruption recovers automatically where technically feasible.
- The wearable runs for a full expected match day.
- Battery replacement is tool-free and does not erase configuration.
- Communication-critical behavior takes priority over logging, indicators, and
  nonessential configuration activity.

## Prototype 0 Product Questions

Prototype 0 should answer the product questions that block hardware design:

1. Can a candidate radio and schedule carry six simultaneous voice sources with
   enough latency and capacity margin?
2. What codec bitrate and packetization interval preserve intelligibility while
   keeping airtime practical?
3. How quickly can the network recover from coordinator loss, member loss, and
   rejoin events?
4. How much current does the candidate architecture consume in coordinator,
   member, idle, worst-case, and poor-link states?
5. Can multiple nearby crews operate without cross-association or unacceptable
   interference?

## Non-Goals For Prototype 0

- Custom wearable enclosure.
- Production battery latch or charging system.
- Release-quality regulatory certification.
- Final industrial design.
- Final audio accessory compatibility.

## Success Evidence

Prototype 0 evidence should include scenario definitions, simulator outputs,
bench traces, latency measurements, packet-loss measurements, airtime
utilization, current measurements, and documented deviations from assumptions.
