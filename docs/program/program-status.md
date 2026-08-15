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
- RT595 promotion evidence now has a checked JSON template and validator.
  Strict promotion refuses compute-only results and requires the full paced
  workload, PLC, zero failures/deadline misses, stack and clock identity, plus
  idle, one-talker, and six-talker current measurements.
- The 114-byte authenticated wrapper, replay window, verified boot-counter
  contract, and FG23 SE Manager/NVM3 adapters are implemented and compile
  against the installed SDK. A stateful secure transport now owns transmit
  counters, replay windows, exhaustion, and failure metrics; the optional FG23
  path protects before scheduling, authenticates before parsing, and refuses
  startup without runtime provisioning. Verified boot-counter advancement is
  now transactionally joined to the crew-key backend, while crew leave aborts
  radio operation and wipes transport/SE state. Application-level admission
  initialization, SE Manager project-component linkage, and live promotion
  remain pending.
- The portable crew-session lifecycle now validates authenticated admission
  results, enforces membership consistency, passes keys through an opaque
  backend, wipes transient key buffers, and fails closed. Device-identity
  pairing and the production secure-key backend remain open.
- The assumed 1,500 mAh power allocation is executable but contains no measured
  load values yet. Its radio-mode baselines now use labeled FGM230S datasheet
  currents plus a separate assumed scheduling/security allowance; duplicate
  JSON keys are rejected rather than silently overwritten.
- Power-budget release now requires structured provenance for every measured
  battery value, reserve factor, and load. Strict evaluation re-hashes each
  bounded evidence artifact and rejects label-only claims, missing captures,
  path escape, or post-capture modification; the present assumed budget still
  correctly fails release despite its positive modeled endurance margin.
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
  readback verification, and fallback to the last valid copy. Its explicit
  16-byte v1 settings schema accepts only approved profile, region,
  calibration, policy, and preferred-volume references while excluding secrets
  and safety authority. The boot runtime restores a valid preference without
  clearing startup/fault mutes, clamps it to the current ceiling, and falls back
  to controlled defaults; Prototype 1 target integration and physical brownout
  injection remain pending.
- The local watchdog gate requires fresh progress from every registered
  communication-critical task, detects stale/missing tasks and timer rollback,
  and withholds the hardware feed on failure. A target-facing driver now owns
  one-time hardware configuration and the physical feed callback, feeds only
  after the portable gate authorizes it, and permanently latches a backend
  failure until controlled reset. The FG23 hardware backend now selects and
  reports a representable watchdog period, remains active through EM1/EM2/EM3,
  locks configuration until reset, and compiles against the production SDK.
  FG23 application progress is reported only after network and optional LC3
  processing returns, and an opt-in deterministic hang injector supports bench
  validation. Startup now captures, classifies, reports, and only then clears
  the FG23 hardware reset cause, making watchdog evidence distinguishable from
  brownout, external, software, lockup, and power-on resets. RT595 callbacks and
  physical injected-hang/reset evidence remain pending.
- The startup supervisor now enforces muted/RF-disabled defaults, bounded rail
  and processor validation, authenticated-boot/configuration/accessory/peer
  interlocks, and crew-session gating before audio and RF operation. Physical
  GPIO and brownout fault-injection evidence remains pending.
- The Prototype 1 portable system runtime now orders startup evaluation, safety
  arbitration, and physical gate application in one control cycle. Cross-module
  testing proves controlled settings/default loading remains silent until all
  startup interlocks pass, and actuation failures latch all gates off until
  reset. Vendor target callbacks and physical timing evidence remain pending.
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
  Production record schema v3 requires a locked state and public fingerprint
  for PASS. Its explicit dual-copy record now has semantic validation,
  corruption fallback, verified writes, and an enabled-SDK-compiled FG23 NVM3
  mapping at `0x0f5230`/`0x0f5231`. The secure identity/debug-lock backend,
  physical power-cut evidence, and fleet revocation service remain pending.
- The fixed signed-update manifest parser validates processor/hardware target,
  newer version and anti-rollback floor, bootloader compatibility, bounded size,
  trusted signature, exact streamed length, and SHA-256 digest before staging.
  A portable staging driver now restricts writes to the inactive slot, verifies
  every chunk by readback, completes digest and independent slot
  authentication, persists pending boot state last, and invalidates/latches on
  any failure. Vendor signature/hash/flash/boot-state callbacks and physical
  power-cut testing remain pending.
- Trial images now have a continuous-health confirmation gate covering clocks,
  persistent storage, watchdog, critical peripherals, peer health, and running
  image authentication. Unhealthy samples or clock rollback restart the full
  soak; confirmed-slot and anti-rollback changes become visible only after a
  successful durable commit, whose failure latches until reset.
- Boot policy now has an explicit 12-byte serialized state over a CRC-protected,
  readback-verified dual-copy store. Runtime writes require a valid prior load,
  factory initialization is distinct, corrupt new generations fall back, and
  generation exhaustion fails without wrap. The FG23 adapter maps isolated
  NVM3 objects `0x0f5220`/`0x0f5221`, fails closed when disabled, and compiles
  enabled against the installed production SDK. RT595 mapping and physical
  power-cut evidence remain pending.
- The local service-session gate now binds authentication to a fresh challenge,
  monotonic counter, role, and exact permission subset; privileged writes require
  physical presence, sessions expire, failures lock out, and counter persistence
  fails closed. Credential/RNG/transport backends remain pending.
- The operational safety arbiter centrally combines power, startup, accessory,
  peer, watchdog, update, service, user, and system-fault inhibits. Exhaustive
  portable combinations pass. Its gate driver now enforces safe transition
  ordering and all-disabled rollback after target callback failure; target
  voice/DMA/radio callback wiring and timing observation remain pending.
- The authenticated crew-admission transcript now binds physical join, fresh
  challenge, coordinator identity, dynamic node/member assignment, roster
  digest, wrapped session key, and a persisted replay counter before secure-key
  activation. Algorithm/trust backends and live multi-device formation remain.
- Coordinator election now supports required durable epoch advancement,
  fail-closed persistence/exhaustion behavior, stale-epoch rejection, and
  deterministic same-epoch convergence. The Prototype 0 overlay still uses the
  explicit volatile-development mode unless requested; the verified-readback
  FG23 NVM3 adapter and overlay switch are implemented, with live power-cut
  testing pending.
- FG23 now has separately keyed, strictly increasing, readback-verified NVM3
  counters for crew admission and service authorization, plus a controlled map
  covering all four monotonic security objects. Live power-cut/endurance tests
  and credential-backend wiring remain pending.
- The FG23 two-slot NVM3 configuration backend is implemented and overlay
  selectable, using isolated exact-length objects while the portable layer owns
  CRC/generation/readback recovery. The concrete v1 schema is implemented;
  brownout/endurance tests remain pending.
- Prototype 1 now has a controlled pre-schematic sheet partition, named power
  domains, safe-state startup contract, protection boundaries, and layout
  constraints. A validated machine-readable contract now fixes sheet ownership,
  cross-domain reset/isolation policy, and mandatory test access. Component
  selection remains correctly gated by measurements.
- Prototype 1 now uses the Secure Vault High FGM230SB SiP as its reversible
  radio schematic baseline. It integrates the crystal, DCDC passives,
  decoupling, and radio match but remains an uncertified 50-ohm external-antenna
  device; body-placement and product FCC testing are not waived.
- The FGM230SB package allocation now accounts for all 48 pins, preserves SWD
  and SWO, carries forward the proven six-wire processor link, enforces the
  manufacturer no-connect and supply-decoupling rules, reserves PTI/UART/timing
  access, and records a reset state for every GPIO. Cross-domain reset ownership
  was reconciled and is machine-checked. A reproducible EDA-neutral symbol pin
  table and manufacturer-derived land-pattern/assembly acceptance requirements
  are controlled. The SPI, diagnostic UART, accessory ADC, optional LFXO, and
  fixed debug routes now pass an executable check against the installed
  production FGM230SB27HGN SDK metadata. A reproducible native KiCad symbol and
  48-pad footprint now match the manufacturer Figure 8.4 geometry and controlled
  allocation, including explicit 80%-area paste apertures. KiCad-native parsing,
  schematic ERC/PCB DRC, and second-reviewer approval remain pending.
- Prototype 1 now has a controlled functional connectivity graph spanning the
  protected pack path, independently measurable rails, fail-safe processor
  isolation, microphone protection/sensing, hardware-limited earpiece output,
  timing access, and the 50-ohm RF boundary. Cross-document validation rejects
  missing contract signals, power-measurement links, unsafe audio bypasses, and
  RF-boundary bypasses; provisional component selections remain explicit.
- Wearable integration now has a machine-readable mechanical contract that
  preserves antenna/battery/audio/service separation and makes battery
  retention, headset strain relief, sealed controls, wearer-inaccessible test
  contacts, and damaged-edge safety non-optional. It reports 13 explicit
  physical-input blockers rather than inventing enclosure dimensions or
  placement; strict release also carries forward AV-015/016/017/018/019/036.
- Production test records now use schema v3 and cannot pass with a partial or
  reordered station sequence. All 13 manufacturing steps, UTC timing, hashed
  limit set, fixture calibration, calibrated measurement instruments, firmware
  hashes, locked identity, and consistent disposition are enforced; fields
  capable of retaining credentials, secrets, or captured audio are rejected.
- Audio-processor promotion evidence now uses schema v2. The validator requires
  real 16 kHz/160-sample ping-pong DMA I/O, one encoder plus five decoders, zero
  capture/playback/pacing faults, the 8 ms compute ceiling, at least 20% stack
  and total-memory margin, three measured current modes, and hashes tying the
  result to its serial log, ELF, and linker map. Compute-only success can no
  longer promote the RT595 platform.
- The audio evidence packager now derives hashes from the actual nonempty
  artifacts, restricts them to the bounded evidence directory, and refuses
  accidental result replacement. Strict promotion validation re-hashes those
  files and rejects missing, moved, escaped, or tampered evidence.
- All 59 controlled SYS/NET/AUD/PWR/FW/MEC requirements now map to valid
  architecture-verification tests. An executable traceability validator rejects
  unknown references, uncovered requirements, and duplicate test identifiers.
- A fail-closed product release manifest now aggregates ten mandatory domains
  and all AV-001 through AV-040 tests. It does not permit waivers, narrow green
  suites cannot imply product completion, and strict release requires complete
  hardware/firmware identity plus successful re-hashing of every evidence
  artifact. The current manifest correctly reports all ten domains blocked.

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
