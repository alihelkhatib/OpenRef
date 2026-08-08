# 20260807 RAILtest Capacity Precheck Result

**Date:** 2026-08-07  
**Status:** Pass as vendor-firmware payload sweep precheck

## Sweep Shape

```mermaid
flowchart LR
  A["Payload 16"] --> B["Payload 60"]
  B --> C["Payload 120"]
  C --> D["Payload 200"]
  D --> E["All at 20 ms, 200 packets"]
```

## Command

```powershell
python tools\railtest_capacity_sweep.py --payloads 16 60 120 200 --packets 200 --tx-delay-ms 20 --settle-seconds 8 --rf-path 0
```

## Metrics

| Payload bytes | Requested | TX complete | RX count | Sync detect | CRC drops | Delivery ratio |
|---:|---:|---:|---:|---:|---:|---:|
| 16 | 200 | 200 | 200 | 200 | 0 | 1.0 |
| 60 | 200 | 200 | 200 | 200 | 0 | 1.0 |
| 120 | 200 | 200 | 200 | 200 | 0 | 1.0 |
| 200 | 200 | 200 | 200 | 200 | 0 | 1.0 |

## Interpretation

The short vendor-firmware payload sweep shows clean bench transport at 20 ms
spacing up to 200 payload bytes on RF path 0.

This does not complete E0-04. The actual E0-04 capacity sweep must run with
OpenRef-owned packet-pair firmware, planned payload/interval ranges, explicit
deadline/failure criteria, and committed summary results.
