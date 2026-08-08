# 20260808 RAILtest Bidirectional Retention Result

## Scope

Medium serialized hardware retention check for the current antenna-connected
FG23-DK2600A bench.

## Bench

| Item | Value |
|---|---|
| Board 1 | COM8 / SEGGER `440320955` |
| Board 2 | COM10 / SEGGER `440320878` |
| RF path | 0 |
| Packet count | 200 each direction |
| Payload | 60 bytes |
| TX delay | 20 ms |
| Command | `python tools\railtest_bidirectional_retention.py --rx-port COM8 --tx-port COM10 --rf-path 0 --packets 200 --payload-bytes 60 --tx-delay-ms 20 --settle-seconds 12 --output-root firmware\prototype0\fg23\results\retention-packet-run --summary-json firmware\prototype0\fg23\results\20260808-railtest-bidirectional-retention-summary.json` |
| Aggregate summary | `firmware/prototype0/fg23/results/20260808-railtest-bidirectional-retention-summary.json` |

## Result

Pass. Both directions completed with 200 transmitted packets, 200 received
packets, delivery ratio `1.0`, zero TX failed packets, and zero RX CRC drops.

| Direction | RX log | TX log | Result |
|---|---|---|---|
| COM10 -> COM8 | `firmware/prototype0/fg23/results/retention-packet-run/20260808-134502-COM10-to-COM8/20260808-railtest-pair-rx.log` | `firmware/prototype0/fg23/results/retention-packet-run/20260808-134502-COM10-to-COM8/20260808-railtest-pair-tx.log` | 200/200, 0 CRC drops |
| COM8 -> COM10 | `firmware/prototype0/fg23/results/retention-packet-run/20260808-134502-COM8-to-COM10/20260808-railtest-pair-rx.log` | `firmware/prototype0/fg23/results/retention-packet-run/20260808-134502-COM8-to-COM10/20260808-railtest-pair-tx.log` | 200/200, 0 CRC drops |

## Interpretation

This is a same-bench retention check for the currently flashed
RAILtest/OpenRef hook image, serial links, antennas, and RF path 0. It does not
replace the one-hour OpenRef AutoRole E0-02 evidence, and it does not complete
E0-05 because no controlled attenuation or shielding step was applied.
