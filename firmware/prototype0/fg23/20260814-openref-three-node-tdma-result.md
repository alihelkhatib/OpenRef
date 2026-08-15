# 20260814 OpenRef Three-Node TDMA Result

**Date:** 2026-08-14  
**Scope:** COM8/node 1, COM10/node 2, COM14/node 4; COM12 preserved for E0-03

## Result

Passed the first live scheduled-network increment on three FG23 development
boards. Each active board transmitted a fixed 78-byte synthetic-audio frame in
its assigned 20 ms superframe slot. Coordinator heartbeats used the reserved
control region.

The measured RAIL TX duration was 1394 us. Against 2500 us slot spacing, the
observed provisional guard was 1106 us.

## Baseline Evidence

After discarding queued UART bytes and capturing from clean resets, all active
nodes converged on one coordinator and reported:

- zero network packet parse failures after convergence;
- zero scheduled-TX failures;
- continuous per-source packet progress;
- no reported sequence gap, duplicate, or stale-frame events.

Raw logs:

- `artifacts/local/2026-08-14-four-board/validation/network-live/fresh-node1-com8.log`
- `artifacts/local/2026-08-14-four-board/validation/network-live/fresh-node2-com10.log`
- `artifacts/local/2026-08-14-four-board/validation/network-live/fresh-node4-com14.log`

## Coordinator Failure and Rejoin

Node 1 was temporarily replaced with a non-network marker image, then restored
with its node-1 network image.

- Node 2 detected the missing coordinator and entered election.
- Node 2 became coordinator at epoch 5.
- Node 4 selected node 2 as coordinator at epoch 5.
- Restored node 1 accepted node 2's higher epoch and became a follower.
- Node 1 did not create a second coordinator.
- Reboot sequence detection accepted node 1's restarted audio sequence.
- Captured transition logs contain zero parse failures, zero scheduled-TX
  failures, and zero stale node-1 frames.

Raw logs:

- `artifacts/local/2026-08-14-four-board/validation/network-live/rejoin-fixed-node1-com8.log`
- `artifacts/local/2026-08-14-four-board/validation/network-live/rejoin-fixed-node2-com10.log`
- `artifacts/local/2026-08-14-four-board/validation/network-live/rejoin-fixed-node4-com14.log`

## Defect Found and Corrected

The first rejoin attempt rejected a rebooted node's reset sequence as stale.
The receive state now treats a small restarted sequence with a backwards source
radio timestamp as a new boot session. The corrected transition produced no
stale node-1 frames.

## Remaining Promotion Work

- Add COM12/node 3 after E0-03 timing capture is preserved.
- Run the four-node 10-minute acceptance test.
- Measure slot starts with the incoming logic analyzer.
- Replace synthetic payload bytes with framed audio samples or codec output.
