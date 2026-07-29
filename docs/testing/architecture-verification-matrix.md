# Architecture Verification Matrix

**Document ID:** OR-TST-002  
**Revision:** 0.1  
**Status:** Draft

| Test ID | Subject | Primary Requirements | Stage | Method |
|---|---|---|---|---|
| AV-001 | Six-user simultaneous audio | SYS-001, NET-002, AUD-008 | Integrated prototype | Test |
| AV-002 | End-to-end latency distribution | SYS-001, AUD-003 | Bench and integrated | Instrumented test |
| AV-003 | Crew formation under time pressure | SYS-005, NET-001 | Integrated | Human-factors demonstration |
| AV-004 | Coordinator loss and failover | SYS-003, NET-003, NET-005 | Integrated | Fault injection |
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
| AV-017 | Wet-hand and glove controls | SYS-014, MEC-003 | Mockup and integrated | Human-factors test |
| AV-018 | Headset disconnect and fault behavior | AUD-006, AUD-007 | Subsystem | Fault injection |
| AV-019 | Listening-level limit | SYS-011, AUD-005 | Integrated | Acoustic measurement |
| AV-020 | Production programming and acceptance | SYS-015, FW-008 | Pilot production | Demonstration |
