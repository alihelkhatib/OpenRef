# Requirements Traceability Framework

**Document ID:** OR-REQ-002  
**Revision:** 0.1  
**Status:** Draft

## Trace Chain

Product need → user story → system requirement → allocated function → architecture decision → design element → verification case → evidence

## Required Traceability Fields

Each controlled requirement shall include:

- requirement ID;
- source;
- priority;
- verification method;
- allocated function or subsystem;
- related hazards;
- related ADRs;
- verification case;
- status.

## Integrity Rules

- No approved system requirement may lack a source.
- No critical or high-priority requirement may lack a planned verification method.
- No safety mitigation may exist only in narrative text.
- No architecture decision may silently invalidate an approved requirement.
- Deleted requirements remain in history with rationale.
