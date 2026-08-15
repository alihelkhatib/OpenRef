# Manufacturing

Manufacturing records must preserve unit traceability, test limits, measured
results, provisioning disposition, firmware identity, and fixture calibration
without exposing private credentials or captured audio.

`production-test-sequence.md` defines the fixture-independent electrical,
audio, RF, recovery, security, programming, and evidence sequence for
Prototype 1.

`production-test-record-template.json` is the schema-v3 station starting point;
`tools/validate_production_test_record.py` fails closed on missing steps,
limits, calibration, identity lifecycle, or privacy boundaries.
