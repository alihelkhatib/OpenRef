# Processor Health and Recovery

**Document ID:** OR-ARC-013
**Revision:** 0.1
**Status:** Portable recovery state machine implemented

The radio and audio processors supervise one another with bounded heartbeat
timeouts. The implementation is
`firmware/system/common/openref_peer_supervisor.h/.c`.

On heartbeat loss, the supervising processor:

1. mutes audio and reports the fault;
2. asserts the failed peer's reset for a configured hold interval;
3. releases reset and waits a bounded boot interval;
4. retries reset only up to the configured attempt count;
5. requests one peer-domain power cycle;
6. enters a persistent failed state if no heartbeat returns.

Any heartbeat received after reset release or power restoration returns the
supervisor to healthy state and clears the retry count. Reset, boot, and power
cycle intervals are target configuration values and must be measured on the
integrated electronics.

The audio side must never continue stale playback during recovery. The radio
side retains crew identity and network credentials while resetting only the
audio processor. A full wearable restart is a final controlled response, not
the first recovery action.

Promotion requires stuck-reset, missing-clock, corrupted-SPI, watchdog,
brownout, and repeated-crash injection on both processors. Logs must prove that
retry counts are bounded and that a failed peer cannot cause an endless reset or
power-cycle loop.
