# Initial Requirements Register

**Document ID:** OR-REQ-003  
**Revision:** 0.1  
**Status:** Draft

This register establishes the highest-level controlled requirements. The existing breadth-first SRS remains the source for detailed decomposition.

| ID | Requirement | Priority | Verification | Source |
|---|---|---|---|---|
| SYS-001 | The system shall support simultaneous full-duplex communication among at least six authorized officials. | Critical | Test | PRD |
| SYS-002 | Core communication shall operate without internet, cloud service, subscription, cellular service, or a connected phone. | Critical | Inspection and test | PRD |
| SYS-003 | The system shall automatically attempt recovery from transient communication interruption. | Critical | Test | User needs |
| SYS-004 | Nearby crews shall remain logically and audibly isolated during normal operation and foreseeable setup error. | Critical | Test | Privacy need |
| SYS-005 | A user shall be able to determine operational readiness before a match without external technical equipment. | High | Demonstration | User story |
| SYS-006 | The primary battery shall be user-replaceable without tools. | High | Demonstration | PRD |
| SYS-007 | Battery replacement shall not erase persistent user or unit configuration. | High | Test | User story |
| SYS-008 | The system shall provide a clear indication of communication degradation requiring user awareness. | Critical | Demonstration and test | HAZ-004 |
| SYS-009 | The system shall prevent unauthorized firmware installation in normal operation. | High | Test and analysis | HAZ-015 |
| SYS-010 | An interrupted firmware update shall not permanently disable recovery of the unit. | High | Test | HAZ-010 |
| SYS-011 | The system shall limit listening output to a validated safe range with approved accessories. | Critical | Test | HAZ-002 |
| SYS-012 | The system shall protect against credible battery overcurrent, overvoltage, undervoltage, and overtemperature conditions. | Critical | Analysis and test | HAZ-001 |
| SYS-013 | A failed or detached wearable unit should not prevent remaining healthy units from communicating where technically feasible. | High | Test | Product priority |
| SYS-014 | Core controls shall be usable with wet hands and representative gloves. | High | Demonstration | Operating environment |
| SYS-015 | The product shall support deterministic production programming and acceptance testing. | High | Demonstration | Manufacturing |
| SYS-016 | Required engineering, service, compatibility, and safety documentation shall be publicly available at release. | High | Inspection | Product values |
| SYS-017 | The radio implementation shall follow an achievable U.S. equipment-authorization path. | Critical | Compliance review | U.S. market |
| SYS-018 | The system shall monitor battery state sufficiently to provide low and critical energy warnings. | High | Test | User need |
| SYS-019 | The system shall preserve communication-critical operation over secondary logging, indicators, or configuration activity. | Critical | Analysis and stress test | Product priority |
| SYS-020 | The system shall expose sufficient diagnostic information to distinguish power, audio, radio, firmware, and accessory fault domains. | Medium | Demonstration | Serviceability |
