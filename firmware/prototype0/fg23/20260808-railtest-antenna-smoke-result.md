# 20260808 RAILtest Antenna-Attached Smoke Result

## Scope

Short serialized hardware sanity check after antennas were attached to both
FG23-DK2600A boards.

## Bench

| Item | Value |
|---|---|
| RX board | COM8 / SEGGER `440320955` |
| TX board | COM10 / SEGGER `440320878` |
| RF path | 0 |
| Packet count | 20 |
| Command | `python tools\railtest_pair_smoke.py --rx-port COM8 --tx-port COM10 --rf-path 0 --packets 20 --output-dir firmware\prototype0\fg23\results` |
| RX log | `firmware/prototype0/fg23/results/20260808-railtest-pair-rx.log` |
| TX log | `firmware/prototype0/fg23/results/20260808-railtest-pair-tx.log` |

## Result

Pass. COM10 reported `transmitted:20` and COM8 logged 20 `rxPacket` events.
COM8 final status reported `RxCount:20`, `RxCrcErrDrop:0`, `FrameErrors:0`,
and `RxOverflow:0`.

## Interpretation

This is a bench-retention smoke check only. It confirms the currently flashed
RAILtest/OpenRef hook image, serial links, RF path 0, and attached antennas are
still functional before continuing fixture-gated work. It does not replace the
long E0-02 runtime evidence or the controlled E0-05 attenuation gate.
