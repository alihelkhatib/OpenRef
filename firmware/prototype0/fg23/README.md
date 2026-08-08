# FG23 Prototype 0 Firmware

Target board: Silicon Labs `FG23-DK2600A`.

This workspace is for the first two-board OpenRef radio prototype. Its job is to
prove deterministic packet transport and timing observability before six-node
network work begins.

## Do Not Commit

- Silicon Labs SDK source copied from an installed SDK.
- Generated Simplicity Studio build directories.
- Local board serial numbers or machine-specific paths.

Record exact SDK source, version, and modifications in `vendor-notes.md` before
committing any vendor-derived file.

## Bring-Up Order

1. Install Simplicity Studio and the selected Gecko SDK.
2. Flash an unmodified Silicon Labs packet example to both boards.
3. Confirm virtual COM logging from both boards.
4. Create the OpenRef two-board packet-pair app from the known-good example.
5. Add OpenRef packet headers and structured serial logs.
6. Add GPIO timing markers for queue, TX start, TX complete, RX complete.
7. Run E0-01, E0-02, and E0-03 from the Prototype 0 entry tests.

Start with [day-one-runbook.md](day-one-runbook.md) when the boards arrive.

## Design Notes

| Document | Purpose |
|---|---|
| [packet-pair-design.md](packet-pair-design.md) | First OpenRef-owned TX/RX packet firmware behavior. |
| [scheduled-tx-design.md](scheduled-tx-design.md) | E0-03 scheduled transmission timing measurement. |
| [simulator-parameter-map.md](simulator-parameter-map.md) | Mapping between simulator assumptions and firmware measurements. |
| [log-format.md](log-format.md) | Structured serial log events. |
| [measurement-plan.md](measurement-plan.md) | Required metrics and evidence naming. |

## Intended Firmware Modes

| Mode | Purpose |
|---|---|
| `packet_pair_tx` | Send timestamped packets at a configured interval. |
| `packet_pair_rx` | Receive packets and log timing, RSSI/LQI, CRC status, and gaps. |
| `scheduled_tx` | Schedule TX relative to local radio time and toggle GPIO markers. |
| `capacity_sweep` | Sweep payload size and interval for measured throughput. |

## Initial Radio Profile

The first profile should match the simulator baseline where the SDK allows it:

- 915 MHz-class operation inside the board's supported range;
- 500 kbps radio bitrate target;
- whitening enabled if supported;
- FEC disabled for the first baseline unless required by the selected PHY;
- conservative TX power for bench testing.

Exact PHY settings must be copied from the SDK project configuration into
`vendor-notes.md`.
