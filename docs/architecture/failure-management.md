# Failure Management Architecture

**Document ID:** OR-ARC-004  
**Revision:** 0.1  
**Status:** Draft

## Principles

- Detect faults close to their source.
- Contain faults before they affect the crew.
- Recover automatically when recovery is safe and deterministic.
- Clearly indicate loss of required capability.
- Preserve a service record without allowing logging to disrupt communication.
- Avoid repeated reboot loops that conceal persistent faults.

## Fault Domains

- power and battery;
- clock and processing;
- radio;
- crew membership;
- audio input;
- audio output;
- storage and configuration;
- firmware integrity;
- controls and indicators;
- accessory connection;
- thermal and environmental.

## Recovery Tiers

1. Retry bounded operation
2. Reinitialize affected module
3. Rejoin or reform crew
4. Controlled subsystem restart
5. Full unit restart
6. Recovery mode
7. Safe shutdown

Each fault shall define maximum retries, timeout, user indication, retained evidence, and escalation behavior.
