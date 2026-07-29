# Security Architecture

**Document ID:** OR-SEC-001  
**Revision:** 0.1  
**Status:** Baseline

## Security Goals

OpenRef shall protect:

- crew membership;
- live voice confidentiality;
- voice and control integrity;
- device identity;
- firmware authenticity;
- recovery from lost or compromised units;
- manufacturing credentials.

## Trust Boundaries

Trust boundaries exist between:

- manufacturing systems and device;
- bootloader and application;
- device and crew network;
- field user and maintenance interface;
- diagnostic logs and exported tools;
- firmware release system and update package.

## Device Identity

Each production unit shall have:

- a unique device identifier;
- a unique cryptographic identity;
- protected key storage appropriate to the selected hardware;
- a revocation or retirement mechanism.

Human-readable serial numbers shall not serve as security credentials.

## Crew Formation

Crew setup shall establish:

- a unique crew session;
- authenticated membership;
- fresh session keys;
- protection against replay;
- explicit indication of successful or failed admission.

The product shall avoid requiring users to manually enter long secrets during normal match setup.

## Voice and Control Protection

- voice packets shall be authenticated and encrypted;
- control traffic shall be authenticated;
- sequence or freshness information shall prevent replay;
- malformed traffic shall be rejected before expensive processing where possible;
- repeated authentication failures shall be rate limited and logged.

## Firmware Security

- firmware images shall be signed;
- the boot chain shall verify authenticity before execution;
- interrupted updates shall preserve a recoverable image;
- rollback policy shall be explicit;
- debug interfaces shall be controlled in production units.

## Manufacturing Provisioning

Provisioning shall:

- create or inject per-device credentials;
- avoid shared fleet-wide private secrets;
- produce an auditable result;
- support failed-unit quarantine;
- prevent credentials from appearing in ordinary production logs.
