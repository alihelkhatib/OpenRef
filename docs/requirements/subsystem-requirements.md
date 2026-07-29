# Preliminary Subsystem Requirements

**Document ID:** OR-REQ-004  
**Revision:** 0.1  
**Status:** Draft

## Radio and Network

| ID | Requirement |
|---|---|
| NET-001 | The network shall admit only authenticated crew members. |
| NET-002 | The network shall support at least six active members. |
| NET-003 | Loss of the current coordinator shall not permanently terminate the crew session. |
| NET-004 | A unit returning after transient loss shall attempt automatic rejoin. |
| NET-005 | Crew identity shall remain stable across coordinator changes. |
| NET-006 | The network shall reject malformed, stale, replayed, or unauthorized control traffic. |
| NET-007 | A nearby independent crew shall not be joined through normal operation or foreseeable setup error. |
| NET-008 | Network-control traffic shall have bounded resource use. |
| NET-009 | Audio transport shall have higher execution priority than nonessential diagnostics or logging. |
| NET-010 | The network shall expose measurable link-quality and recovery information for engineering diagnostics. |

## Audio

| ID | Requirement |
|---|---|
| AUD-001 | The audio subsystem shall capture speech from the approved headset microphone. |
| AUD-002 | The audio subsystem shall limit clipping and recover from overload. |
| AUD-003 | The audio subsystem shall support speech bandwidth sufficient for officiating intelligibility. |
| AUD-004 | The audio subsystem shall mix or combine remote speech without arithmetic overflow or sustained distortion. |
| AUD-005 | The user shall be able to adjust listening volume within validated limits. |
| AUD-006 | A disconnected or failed microphone shall not produce uncontrolled noise to the crew. |
| AUD-007 | The audio subsystem shall indicate or log detectable accessory faults. |
| AUD-008 | Audio processing shall remain stable under worst-case simultaneous speech. |

## Power

| ID | Requirement |
|---|---|
| PWR-001 | The wearable shall operate for at least eight hours under the defined representative duty cycle. |
| PWR-002 | The battery shall be replaceable without tools. |
| PWR-003 | Reverse or incorrect battery insertion shall not damage the wearable. |
| PWR-004 | The system shall detect low and critical energy states. |
| PWR-005 | The system shall enter a controlled safe state before energy loss can corrupt persistent data. |
| PWR-006 | Charging shall be inhibited outside validated temperature and voltage limits. |
| PWR-007 | A battery fault shall be contained from unrelated system domains where practical. |

## Firmware Platform

| ID | Requirement |
|---|---|
| FW-001 | The platform shall start into a defined state after normal reset, watchdog reset, and brownout reset. |
| FW-002 | Firmware images shall be authenticated before activation. |
| FW-003 | An interrupted update shall leave at least one bootable recovery path. |
| FW-004 | Watchdogs shall detect and recover from loss of critical execution. |
| FW-005 | Persistent configuration shall use a versioned format. |
| FW-006 | Communication-critical processing shall have bounded scheduling latency. |
| FW-007 | Diagnostic recording shall not exhaust storage or block communication-critical processing. |
| FW-008 | Production identity and cryptographic material shall be provisioned through a controlled process. |

## Mechanical and Environmental

| ID | Requirement |
|---|---|
| MEC-001 | The wearable shall retain the battery during representative running, impacts, and drops. |
| MEC-002 | The enclosure shall protect internal electronics from rain, sweat, and incidental mud exposure. |
| MEC-003 | User controls shall resist accidental activation during normal wear. |
| MEC-004 | The mounting system shall remain secure during running and directional changes. |
| MEC-005 | The headset connection shall include appropriate strain relief. |
| MEC-006 | The enclosure shall not expose sharp edges in normal or foreseeable damaged states. |
