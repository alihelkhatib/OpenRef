# FG23 Setup Notes

## Required Hardware

- 2x Silicon Labs `FG23-DK2600A` boards.
- 2x USB data cables.
- USB current measurement path.
- Logic analyzer or oscilloscope for GPIO timing.

## Required Software

- Simplicity Studio.
- Gecko SDK selected for the first bring-up.
- Serial terminal capable of logging both virtual COM ports, or
  `tools/capture_serial.py`.
- Git working tree with this repository.

## Toolchain Record

Fill this in during first setup:

| Item | Value |
|---|---|
| Simplicity Studio version | TBD |
| Gecko SDK version | TBD |
| Board 1 serial | Local note only; do not commit if personally identifying |
| Board 2 serial | Local note only; do not commit if personally identifying |
| Host OS | TBD |
| Compiler/toolchain version | TBD |

## First Flash Checklist

- [ ] Install Simplicity Studio.
- [ ] Install selected Gecko SDK.
- [ ] Connect one board and confirm debugger detection.
- [ ] Build a vendor packet radio example without modifications.
- [ ] Flash board 1.
- [ ] Flash board 2.
- [ ] Capture serial output from both boards.
- [ ] Record exact example name and SDK path in `vendor-notes.md`.
- [ ] Commit only OpenRef notes/configuration, not copied SDK source.

List ports from repository root:

```bash
python tools/capture_serial.py --list
```

Capture a short log:

```bash
python tools/capture_serial.py \
  --port COM7 \
  --baud 115200 \
  --duration-seconds 120 \
  --output firmware/prototype0/fg23/results/YYYYMMDD-node-1-e0-01.log
```
