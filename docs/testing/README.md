# OpenRef Testing

This directory contains verification strategy, test plans, test case templates,
and early Prototype 0 evidence.

## Key Documents

| Document | Purpose |
|---|---|
| [verification-strategy.md](verification-strategy.md) | Overall verification approach. |
| [architecture-verification-matrix.md](architecture-verification-matrix.md) | Links architecture subjects to requirements and methods. |
| [product-release-manifest.json](product-release-manifest.json) | Fail-closed product gate spanning every AV-001 through AV-040 result. |
| [prototype-0-test-plan.md](prototype-0-test-plan.md) | Six-node network feasibility test plan. |
| [prototype-0-entry-tests.md](prototype-0-entry-tests.md) | Board-level tests before full protocol implementation. |
| [fg23-watchdog-reset-test.md](fg23-watchdog-reset-test.md) | Controlled injected-hang, reset attribution, and timing procedure. |
| [prototype-0-simulator-screening.md](prototype-0-simulator-screening.md) | Simulator sweep method and initial screening result. |
| [test-case-template.md](test-case-template.md) | Template for controlled test procedures. |

Validate the current manifest structure and list its real blockers with:

```text
python tools/validate_product_release_manifest.py \
  docs/testing/product-release-manifest.json
```

A release candidate must use `--require-release --artifact-root DIRECTORY`.
Strict mode requires all ten domains to pass, complete AV-001 through AV-040
coverage, complete release/build identity, and successful re-hashing of every
recorded evidence file. This release has no `WAIVED` state.
