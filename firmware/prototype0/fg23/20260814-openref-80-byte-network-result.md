# FG23 80-byte LC3 payload network result (2026-08-14)

## Result

The promoted 80-byte audio payload passed a live three-board scheduled-network
run and coordinator reset/rejoin test. Each on-air frame was 98 bytes: the
18-byte OpenRef header plus space for two 40-byte LC3 frames.

## Hardware

| Node | Port | Debug serial |
|---:|---|---:|
| 1 | COM8 | 440320955 |
| 2 | COM10 | 440320878 |
| 4 | COM14 | 440320958 |

COM12 was deliberately left on the E0-03 GPIO-marker image.

## Continuous Exchange

A synchronized 60-second capture produced:

- node 1: at least 7,000 received packets;
- node 2: at least 7,750 received packets;
- node 4: at least 7,500 received packets;
- parse failures: 0 on every node;
- schedule failures: 0 on every node;
- coordinator agreement: node 1, epoch 0.

The receive rate includes remote audio frames and coordinator heartbeats.

## Coordinator Reset and Rejoin

Resetting node 1 kept it unavailable beyond the coordinator timeout. Node 2
reported timeout action 2 followed by coordinator-change/heartbeat actions 5
and became coordinator at epoch 1. Node 4 reported actions 2 then 4 and followed
node 2.

After node 1 restarted, all three nodes reported coordinator 2, epoch 1. The
returning lower-ID node did not reclaim coordination. Final captures retained
zero parse and scheduling failures.

## Remaining Promotion Work

- repeat on all four boards after E0-03 marker capture;
- run the required 10-minute continuous four-board test;
- inject real LC3 bytes through the processor link rather than deterministic
  synthetic payload;
- confirm the 832 us modeled slot guard with the external logic analyzer.

