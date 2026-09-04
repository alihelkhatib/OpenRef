# Architecture Verification Evidence Manifest

The MVP readiness audit does not treat a planned test, traceability mapping, or
narrative status as proof that a requirement was verified. Supply
`tools/audit_mvp_readiness.py` with a reviewed JSON manifest that has one
passing, hash-bound result for every `AV-*` row in
`architecture-verification-matrix.md`:

```text
python tools/audit_mvp_readiness.py \
  --prototype0-root <canonical-prototype0-root> \
  --audio-result <paced-target-result.json> \
  --verification-result <verification-evidence.json>
```

The minimum manifest shape is:

```json
{
  "schema": "openref-architecture-verification-evidence-v2",
  "matrix_sha256": "64-lowercase-hex-digits",
  "results": [
    {
      "id": "AV-001",
      "status": "passed",
      "procedure": "OR-TP-001 revision 2",
      "conclusion": "All acceptance criteria passed with no deviations.",
      "executor": "Test Operator",
      "executed_at": "2026-08-20T12:00:00Z",
      "configuration": {
        "hardware_revision": "EVT1",
        "firmware_revision": "0123456789abcdef"
      },
      "reviewer": {
        "name": "Independent Reviewer",
        "reviewed_at": "2026-08-20T13:00:00Z"
      },
      "evidence": [
        {
          "path": "raw/av-001-controlled-run.log",
          "sha256": "64-lowercase-hex-digits",
          "bytes": 12345,
          "role": "raw-observation",
          "media_type": "text/plain"
        }
      ]
    }
  ]
}
```

Relative artifact paths resolve from the manifest directory, allowing the
manifest and raw evidence archive to remain outside the source checkout. The
audit rejects missing or duplicate test IDs, non-passing statuses, absent
procedure/conclusion/executor/revision/reviewer provenance, empty evidence
lists, unreadable artifacts, malformed hashes, and content whose current byte
count or SHA-256 does not match the reviewed manifest. Timestamps use UTC
RFC3339 seconds (`YYYY-MM-DDTHH:MM:SSZ`). A hash proves artifact identity; it
does not prove that an artifact came from hardware or that its conclusion is
correct. The matrix digest also prevents carrying old passes into a changed
verification matrix, and the reviewer identity must differ from the executor.

To inventory outputs before review, create a deliberately non-passing package:

```text
python tools/collect_architecture_verification_evidence.py \
  --output <archive>/verification-evidence.json \
  --artifact AV-008=<native-or-target-stress-output>
```

The collector records repository state, matrix metadata, byte counts, hashes,
roles, and media types, but emits every row as `unverified`. It cannot promote
an automated build, native unit-test transcript, or vendor correspondence into
physical or integrated evidence.

One artifact may support multiple tests when an integrated procedure genuinely
covers them, but each matrix row must have an explicit result. Preserve the
procedure, raw observations, configuration, equipment identity/calibration,
software and hardware revisions, analysis output, deviations, and reviewer
approval needed to interpret each claimed pass.
