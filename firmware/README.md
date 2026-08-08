# OpenRef Firmware

Firmware work starts with Prototype 0 network feasibility.

## Layout

| Path | Purpose |
|---|---|
| `common/` | Vendor-independent headers, packet formats, and shared contracts. |
| `prototype0/fg23/` | Silicon Labs FG23-DK2600A bring-up workspace and notes. |

## Current Hardware Target

Prototype 0 lead platform:

- Silicon Labs `FG23-DK2600A`
- 868-915 MHz development kit
- two-board entry tests first
- six-node expansion only after deterministic packet transport is demonstrated

Do not commit Silicon Labs SDK source or generated IDE artifacts unless their
license and exact origin are recorded.
