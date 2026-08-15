# Listening-Level Control

**Document ID:** OR-AUD-006
**Revision:** 0.1
**Status:** Software policy implemented; acoustic calibration pending

OpenRef uses layered output protection. No single software value is treated as
proof of a safe listening level.

## Layers

1. A hardware output-gain and voltage ceiling limits the worst credible output
   even if firmware fails.
2. The codec configuration exposes only a calibrated, monotonic gain table.
3. `firmware/system/common/openref_volume_manager.h/.c` enforces a safe boot
   step, absolute step ceiling, downward-only temporary ceiling, and independent
   mute reasons.
4. The audio mixer limiter prevents numeric overload and reports clipping.
5. Headset open/short, system fault, shutdown, and peer recovery independently
   assert mute; clearing one reason cannot clear another.

Lowering a temporary ceiling also lowers the remembered requested step. Removing
the ceiling therefore cannot cause a sudden volume rebound. Startup begins muted
and cannot produce output until the target adapter explicitly clears the startup
reason after codec clocks and DMA are stable.

## Calibration gate

The Q15 gain table and maximum step remain unset until the approved minimum-
impedance earpiece is measured with the production codec, supply range, output
network, coupler, and representative program material. Software unity gain is
not an acoustic safety limit.

Calibration evidence must include fixture identity, coupler and meter
calibration, headset sample spread, maximum continuous and transient level,
startup/shutdown/cable-fault impulses, and the exact firmware/codec register
configuration. Human listening is prohibited until dummy-load electrical tests
and the conservative acoustic ceiling pass.
