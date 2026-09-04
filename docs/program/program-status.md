# OpenRef Program Status

**Document ID:** OR-PGM-001  
**Revision:** 0.5
**Status:** Draft

## Product Scope Assumption

Version 1 is intended for sale, distribution, testing, and operation in the United States.

Pennsylvania is the initial development and field-validation environment. The design shall not rely on Pennsylvania-specific radio privileges or venue infrastructure.

## Current Milestones

- Product definition: substantially complete
- Engineering standards: initial draft complete
- Functional architecture: initial draft complete
- Requirements refinement: in progress
- Technology architecture: in progress; FG23 radio plus separate audio processor selected
- Detailed design: in progress for protocol, processor link, audio mixer, and power tree
- Prototype implementation: Prototype 0 radio network active on three boards;
  fourth board reserved for external timing capture

## Current Evidence

- E0-01 toolchain and E0-02 one-hour packet pair passed.
- Three-board scheduled network passes the final 80-byte LC3 payload size with
  zero parse or schedule failures in the latest capture.
- Coordinator reset, replacement, and returning-node rejoin passed.
- LC3 runs on FG23 but misses the six-participant compute deadline; the measured
  result establishes a separate audio processor.
- The fixed FG23/audio-processor link, real-payload packet path, and bounded
  five-source mixer are implemented.
- The full-duplex processor-link transaction policy is implemented with audio
  priority, bounded queues, valid idle transfers, request-line semantics, and
  corruption/sequence-gap diagnostics; target SPI/DMA adapters remain pending.
- The target-facing 10 ms audio runtime is implemented with capture-gap,
  codec-failure, and 8 ms deadline diagnostics.
- The 114-byte authenticated wrapper, replay window, verified boot-counter
  contract, and FG23 SE Manager/NVM3 adapters are implemented and compile
  against the installed SDK. Live secured-radio promotion is pending.
- The portable crew-session lifecycle now validates authenticated admission
  results, enforces membership consistency, passes keys through an opaque
  backend, wipes transient key buffers, and fails closed. Device-identity
  pairing and the production secure-key backend remain open.
- The assumed 1,500 mAh power allocation is executable but contains no measured
  load values yet.
- The portable power supervisor implements warning, critical grace, hard-cutoff,
  thermal, sensor-fault, and pack-removal latch behavior; its thresholds await
  pack selection and discharge calibration.
- The portable peer supervisor implements bounded reset retries, one domain
  power-cycle request, stale-audio muting, and persistent failure reporting.
- A bounded 32-record diagnostic ring and explicit 16-byte export format cover
  radio, audio, power, recovery, and assertion events without voice or key data.
- The output-volume policy enforces startup mute, calibrated monotonic steps,
  independent fault mutes, absolute ceilings, and no rebound after derating.
- The portable A/B boot policy enforces authenticated-slot eligibility,
  anti-rollback versions, persisted bounded trials, confirmation, and fallback;
  vendor bootloader and flash adapters remain pending.
- The versioned configuration store uses two CRC-protected generations,
  readback verification, and fallback to the last valid copy; target flash
  adapters and physical brownout injection remain pending.
- The local watchdog gate requires fresh progress from every registered
  communication-critical task, detects stale/missing tasks and timer rollback,
  and withholds the hardware feed on failure. FG23 and RT595 hardware-watchdog
  adapters and injected-hang evidence remain pending.
- The startup supervisor now enforces muted/RF-disabled defaults, bounded rail
  and processor validation, authenticated-boot/configuration/accessory/peer
  interlocks, and crew-session gating before audio and RF operation. Physical
  GPIO and brownout fault-injection evidence remains pending.
- The semantic status policy separates base operating state from battery, link,
  and accessory alerts; computes truthful readiness; prioritizes faults and
  recovery; and generates edge-triggered attention events. Physical patterns
  and wet/glove/visibility human-factors validation remain pending.
- The four-input button filter provides configurable debounce, one-shot
  protected long-press detection, simultaneous-button handling, and fail-quiet
  timer rollback. Physical control mapping and human-factors timing remain open.
- The accessory monitor applies hysteretic, persistence-filtered disconnected,
  microphone-open/short, and sensor-fault classification while requesting mute
  immediately on raw unsafe input. Circuit-specific thresholds and wet-fault
  calibration remain pending.
- The per-bay charger supervisor independently gates charging on pack identity,
  voltage, temperature, sensor health, charger status, and elapsed time, with
  faults latched until pack removal. Charger hardware and pack-derived limits
  remain pending.
- The device lifecycle enforces ordered factory test, internal identity
  generation, production debug lock, quarantine, and irreversible retirement.
  Production record schema v2 requires a locked state and public fingerprint
  for PASS; the secure backend and fleet revocation service remain pending.
- The fixed signed-update manifest parser validates processor/hardware target,
  newer version and anti-rollback floor, bootloader compatibility, bounded size,
  trusted signature, exact streamed length, and SHA-256 digest before staging.
  Vendor signature/hash/flash adapters and power-cut testing remain pending.
- The local service-session gate now binds authentication to a fresh challenge,
  monotonic counter, role, and exact permission subset; privileged writes require
  physical presence, sessions expire, failures lock out, and counter persistence
  fails closed. Credential/RNG/transport backends remain pending.
- The operational safety arbiter centrally combines power, startup, accessory,
  peer, watchdog, update, service, user, and system-fault inhibits. Exhaustive
  portable combinations pass; target voice/DMA/radio gate wiring and timing
  observation remain pending.
- Prototype 1 now has a controlled pre-schematic sheet partition, named power
  domains, safe-state startup contract, protection boundaries, and layout
  constraints. Component selection remains correctly gated by measurements.
- All 59 controlled SYS/NET/AUD/PWR/FW/MEC requirements now map to valid
  architecture-verification tests. An executable traceability validator rejects
  unknown references, uncovered requirements, and duplicate test identifiers.

## Immediate Open Gates

- E0-03 external GPIO timing capture after the ordered logic analyzer arrives;
- current waveforms for FG23 operating modes;
- RT595 LC3, mixer, audio-I/O, and processor-link benchmark;
- controlled attenuation/body-placement evidence;
- four-board ten-minute final-payload run after E0-03;
- mechanical volume, connector, antenna, battery, controls, and sealing inputs.

## Current Decision Authority

The project may proceed autonomously on reversible engineering-process decisions.

Product-owner approval is required for decisions that materially change:

- intended users;
- core match experience;
- target retail price;
- supported crew size;
- expected operating duration;
- physical form factor;
- privacy model;
- market geography;
- licensing strategy;
- risk acceptance.
