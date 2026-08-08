# FG23 Two-Board Bring-Up Checklist

## E0-01 Toolchain Reproduction

- [ ] Fresh checkout builds the chosen vendor example.
- [ ] Board 1 flashes successfully.
- [ ] Board 2 flashes successfully.
- [ ] Both boards expose virtual COM ports.
- [ ] Serial logs are captured to files.
- [ ] Toolchain versions are recorded.

Evidence:

- build log;
- flash/programming log;
- serial capture from each board;
- screenshot or text export showing detected boards.

## E0-02 Continuous Packet Pair

Minimum run: 1 hour.

Board A:

- [ ] sends sequence-numbered timestamp packets;
- [ ] logs `tx_queued`;
- [ ] logs `tx_started`;
- [ ] logs `tx_done`.

Board B:

- [ ] logs `rx_done`;
- [ ] records sequence number;
- [ ] records local receive timestamp;
- [ ] records RSSI/LQI/CRC metadata when available;
- [ ] records sequence gaps.

Pass condition:

- no unexplained resets;
- no unbounded queue growth;
- packet loss and gap count recorded;
- inter-arrival min, mean, p95, p99, and max can be computed.

Analyze receiver logs with:

```bash
python tools/analyze_packet_pair.py \
  firmware/prototype0/fg23/results/YYYYMMDD-e0-02-packet-pair.csv \
  --json firmware/prototype0/fg23/results/YYYYMMDD-e0-02-summary.json
```

## E0-03 Scheduled Transmission

- [ ] Schedule repeated transmissions relative to radio/local time.
- [ ] Toggle GPIO when packet is queued.
- [ ] Toggle GPIO when TX starts.
- [ ] Toggle GPIO when TX completes.
- [ ] Capture at least 100 timing samples.

Pass condition:

- scheduled TX acceptance/failure is logged;
- TX launch error distribution is measurable;
- timing markers correspond to serial log events.

## Stop Conditions

Stop and fix before continuing if:

- flashing is not repeatable;
- virtual COM logging is unreliable;
- either board resets during a one-hour packet-pair run;
- scheduled TX timing cannot be observed;
- radio metadata needed for later tests is unavailable.
