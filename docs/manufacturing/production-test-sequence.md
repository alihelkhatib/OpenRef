# Prototype 1 Production Test Sequence

**Document ID:** OR-MFG-002
**Revision:** 0.2
**Status:** Fixture-independent baseline

Every assembled wearable must produce an attributable, machine-readable pass or
fail record before enclosure integration. Rework does not erase the original
failure; attempts remain linked to the unit serial number and PCB lot without
storing crew credentials or audio.

## Fixture interfaces

The board provides normally unpopulated access to ground, protected fixture
input, domain current shunts, SWD/reset for both processors, serial diagnostics,
processor-link signals, timing markers, battery/temperature/power-good nodes,
headset stimulus and measurement, and a conducted or shielded RF path.

Fixture power is current- and voltage-limited. It must not coexist with a source
that can backfeed VMCU, 3.3 V, or the battery contact.

## Ordered sequence

1. Scan the PCB lot and assign the immutable device identifier.
2. Inspect shorts and verify unpowered resistance against guarded limits.
3. Apply current-limited power; reject excessive inrush or rail error.
4. Program and verify signed radio and audio factory-test images.
5. Read identity and security capability without exporting private keys.
6. Measure sleep, radio-idle/RX/TX, audio-idle, and audio-active currents through
   separate domain shunts.
7. Exercise processor SPI at production rate with CRC, overflow, interrupt, and
   peer-reset fault injection.
8. Run acoustic stimulus through capture, codec, playback, and earpiece load;
   measure gain, distortion, noise, continuity, and safe maximum output.
9. Run shielded RF frequency, output-power, packet-error, receive-sensitivity,
   and antenna-path continuity tests.
10. Exercise controls, indicators, vibration, pack-present, temperature,
    power-good, and recovery straps.
11. Inject watchdog, sensor, undervoltage, and heartbeat failures; verify
    diagnostic codes and bounded recovery.
12. Provision production identity only after hardware passes, install release
    images, apply production debug policy, and verify authenticated boot.
13. Export and inspect diagnostics, clear factory data according to policy, and
    create the final result label.

## Machine-readable record

Each step records test ID, limit-set revision, firmware hashes, fixture and
station IDs, timestamps, numeric measurements with units, pass/fail, and failure
code. Calibration-sensitive steps include instrument ID and calibration due
date. Final disposition is `PASS`, `REWORK`, `SCRAP`, or `QUARANTINE`.
Provisioning anomalies always produce `QUARANTINE`.

Current, RF, acoustic, thermal, and timing limits remain unset until prototype
measurements exist. An empty limit must never default to pass.

Start each attempt from `production-test-record-template.json`. The template is
intentionally not a passing record: timestamps, controlled limits,
measurements, instrument evidence, images, identity, and disposition must be
populated by the station.

`tools/validate_production_test_record.py` enforces the baseline record rules:
unique test IDs, bounded measurements when limits are required, valid firmware
SHA-256 identifiers, failure codes, authorized skips, disposition consistency,
mandatory quarantine for provisioning anomalies, and the device-identity
lifecycle contract in `OR-MFG-003`. Record schema version 3 requires all 13
steps exactly in order, attempt and step UTC timestamps, a hashed limit set,
fixture calibration, and calibrated instrument records for resistance, power,
current, acoustic, and RF steps. It rejects fields that could store private
keys, credentials, provisioning blobs, recovery secrets, or captured audio.
A passing record requires the `PRODUCTION_LOCKED` state and the public
16-hex-character `identity_fingerprint`.
