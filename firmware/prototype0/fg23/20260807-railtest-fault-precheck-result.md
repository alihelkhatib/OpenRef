# 20260807 RAILtest Fault-Recovery Precheck Result

**Date:** 2026-08-07  
**Status:** Pass as safe vendor-firmware precheck

## Scope

This precheck uses safe RAILtest operations only:

- RX enable;
- RX disable;
- TX cancellation with `txCancel`;
- final `status` check.

It intentionally avoids destructive commands such as forced assert/reset.

## Commands

```powershell
python tools\railtest_fault_probe.py --port COM8 --rf-path 0 --summary-json firmware\prototype0\fg23\results\20260807-railtest-fault-probe-com8.json
python tools\railtest_fault_probe.py --port COM10 --rf-path 0 --summary-json firmware\prototype0\fg23\results\20260807-railtest-fault-probe-com10.json
```

## Metrics

| Board port | RF state after probe | User TX aborted | User TX blocked | User TX underflow | RX overflow | Frame errors |
|---|---|---:|---:|---:|---:|---:|
| COM8 | Idle | 1 | 0 | 0 | 0 | 0 |
| COM10 | Idle | 1 | 0 | 0 | 0 | 0 |

## Interpretation

Both boards returned to idle after safe cancellation exercises. This supports
the basic RAIL control path but does not complete E0-06.

Full E0-06 still requires OpenRef-owned firmware hooks for:

- transmit cancellation;
- receive cancellation;
- malformed packet handling;
- queue saturation;
- forced radio reset;
- bounded memory/event queue verification.
