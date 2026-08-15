# Prototype 1 Power Tree

**Document ID:** OR-PWR-003  
**Revision:** 0.1  
**Status:** Architecture baseline; component values pending measurements

## Source

Prototype 1 uses a removable, protected, single-cell rechargeable lithium-ion
pack. The initial capacity envelope is 1,500 mAh nominal. Normal charging occurs
in a separate multi-bay charger, preserving the sealed wearable boundary and
allowing immediate pack replacement.

The pack interface provides positive, negative, temperature sense, and an
optional identification contact. Pack protection covers overcharge,
overdischarge, overcurrent, and short circuit. Reverse insertion is prevented
mechanically and electrically.

## Domains

```text
protected 1S pack
  -> input current limit and reverse blocking
  -> system load switch with ship mode
     -> radio regulator -> FG23 and RF matching
     -> audio regulator -> audio processor core and I/O rails
     -> codec regulator -> codec, microphone bias, headphone output
     -> always-on monitor -> pack voltage, temperature, latch/wake input
```

Radio and audio domains are independently measurable and resettable. The
always-on domain owns hard undervoltage shutdown and does not depend on either
application processor behaving correctly.

## Required Schematic Features

- reverse-current blocking with voltage drop included in the budget;
- input transient suppression appropriate to exposed battery contacts;
- regulator enable and power-good signals routed to test pads;
- removable zero-ohm links or shunts for each domain's current measurement;
- audio filtering that prevents TDMA current bursts entering the headset;
- independent processor reset and watchdog paths;
- battery voltage and temperature measurement valid during TX bursts;
- a true ship state compatible with six-month storage;
- conservative brownout thresholds that mute audio before corrupt operation.

## Fault Behavior

| Fault | Required response |
|---|---|
| Pack removed | Safe shutdown; crew identity retained in nonvolatile memory |
| Pack inserted | Controlled startup without contact damage |
| Radio rail fault | Audio muted and fault indicated |
| Audio rail fault | Radio remains able to report the fault |
| Low battery | At least 45 minutes representative operation remaining |
| Critical battery | At least 10 minutes warning, then deterministic mute and shutdown |
| Processor hang | Reset the failed peer first; power-cycle only after bounded retries |
| Overtemperature | Reduce load or shut down before cell or enclosure limits are exceeded |

The bounded processor recovery sequence is implemented by `OR-ARC-013`; target
adapters provide the physical reset, power-domain, mute, and heartbeat signals.

## Sizing Gate

No regulator, cell, protection IC, connector rating, or copper width is final
until these waveforms are captured:

1. FG23 RX baseline and scheduled +14 dBm TX burst;
2. audio processor encode/decode/mix workload;
3. approved headset at minimum impedance and maximum allowed output;
4. startup, coordinator transition, update, and fault recovery;
5. low-temperature and aged-cell voltage sag.

The executable allocation is `prototype1-assumed-budget.json`; every load is
currently marked assumed.

The hardware-independent warning and shutdown behavior is implemented in
`firmware/system/common/openref_power_supervisor.h/.c` and specified by
`OR-PWR-004`. Its voltage and temperature thresholds remain calibration inputs,
not component-selection evidence.
