# Architecture Verification Matrix

**Document ID:** OR-TST-002  
**Revision:** 0.3
**Status:** Draft

| Test ID | Subject | Primary Requirements | Stage | Method |
|---|---|---|---|---|
| AV-001 | Six-user simultaneous audio | SYS-001, NET-002, AUD-004, AUD-008 | Integrated prototype | Test |
| AV-002 | End-to-end latency distribution | SYS-001, AUD-003 | Bench and integrated | Instrumented test |
| AV-003 | Crew formation under time pressure | SYS-005, NET-001 | Integrated | Human-factors demonstration |
| AV-004 | Coordinator loss, persisted epoch advance, split-brain convergence, and failover | SYS-003, NET-003, NET-005 | Integrated | Power-cut, partition, and persistence fault injection |
| AV-005 | Unit temporary loss and rejoin | SYS-003, NET-004 | Integrated | RF interruption test |
| AV-006 | Nearby crew isolation | SYS-004, NET-007 | Integrated | Multi-crew test |
| AV-007 | Unauthorized join and replay rejection | SYS-004, NET-006 | Subsystem and integrated | Security test |
| AV-008 | Continuous worst-case speech load | SYS-019, AUD-008 | Bench | Stress test |
| AV-009 | Representative endurance | PWR-001, SYS-018 | Integrated | Power profile test |
| AV-010 | Low and critical battery warning | SYS-018, PWR-004 | Integrated | Controlled discharge |
| AV-011 | Battery replacement recovery | SYS-006, SYS-007 | Integrated | Demonstration |
| AV-012 | Interrupted firmware update | SYS-010, FW-003 | Subsystem | Fault injection |
| AV-013 | Invalid firmware rejection | SYS-009, FW-002 | Subsystem | Security test |
| AV-014 | Logging saturation | SYS-019, FW-007 | Subsystem | Stress test |
| AV-015 | Rain and sweat exposure | MEC-002 | Engineering prototype | Environmental test |
| AV-016 | Drop and battery retention | MEC-001 | Engineering prototype | Mechanical test |
| AV-017 | Wet-hand, glove, bounce, hold, and accidental control activation | SYS-014, MEC-003 | Mockup and integrated | Electrical injection and human-factors test |
| AV-018 | Headset disconnect, open, short, wet leakage, and sense-fault behavior | AUD-006, AUD-007 | Subsystem | Electrical fault injection |
| AV-019 | Listening-level limit | SYS-011, AUD-005 | Integrated | Acoustic measurement |
| AV-020 | Production programming and acceptance | SYS-015, FW-008 | Pilot production | Demonstration |
| AV-021 | Bounded peer reset and power-cycle recovery | SYS-019, FW-005 | Subsystem and integrated | Fault injection |
| AV-022 | Diagnostic saturation, service authorization, expiry, replay, lockout, and sensitive-data exclusion | SYS-020, FW-007 | Subsystem | Stress, fault injection, and security inspection |
| AV-023 | Undervoltage, sensor fault, and overtemperature shutdown | SYS-012, PWR-004 | Power subsystem | Fault injection |
| AV-024 | Secured 114-byte airtime and replay behavior | NET-002, NET-006 | Radio subsystem | Instrumented security test |
| AV-025 | Configuration torn-write fallback, schema rejection, and endurance | FW-005 | Subsystem | Fault injection and analysis |
| AV-026 | Operation without external infrastructure | SYS-002 | Integrated prototype | Inspection and disconnect test |
| AV-027 | Degradation indication and link diagnostics | SYS-008, NET-010 | Integrated prototype | RF impairment test and demonstration |
| AV-028 | Failed-node isolation | SYS-013 | Integrated prototype | Fault injection |
| AV-029 | Public release-document completeness | SYS-016 | Release candidate | Inspection |
| AV-030 | U.S. radio authorization path | SYS-017 | Engineering prototype | Compliance review |
| AV-031 | Microphone capture, overload, and mixer saturation | AUD-001, AUD-002 | Audio subsystem | Electrical and acoustic test |
| AV-032 | Bounded control traffic and communication scheduling | SYS-019, NET-008, NET-009, FW-006 | Subsystem | Instrumented stress test |
| AV-033 | Reset-state and per-task watchdog recovery | FW-001, FW-004 | Subsystem | Reset, task hang, starvation, and boot-loop fault injection |
| AV-034 | Battery replacement, reverse insertion, safe shutdown, and fault containment | PWR-002, PWR-003, PWR-005, PWR-007 | Power subsystem | Demonstration and fault injection |
| AV-035 | Charger voltage, temperature, and bay-fault protection | PWR-006 | Charging subsystem | Fault injection |
| AV-036 | Mount retention, headset strain relief, and damaged-edge safety | MEC-004, MEC-005, MEC-006 | Engineering prototype | Mechanical test and inspection |
| AV-037 | Startup sequencing and operational interlocks | FW-001, FW-002, PWR-005, NET-001 | Subsystem and integrated | Reset, brownout, invalid-state, and session-loss fault injection |
| AV-038 | Status priority, readiness truthfulness, and one-shot attention | SYS-005, SYS-008, SYS-018, SYS-020 | Subsystem and human factors | State injection and demonstration |
| AV-039 | Cross-subsystem mute and RF-inhibit arbitration | SYS-008, SYS-019, AUD-006, PWR-005, FW-006 | Subsystem and integrated | Exhaustive state injection and timing observation |
| AV-040 | Physical-intent crew admission, wrong-crew isolation, replay, and wrapped-key activation | SYS-004, NET-001, NET-006, NET-007 | Network and security subsystem | Transcript fault injection and multi-crew test |
