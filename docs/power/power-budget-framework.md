# Power Budget Framework

**Document ID:** OR-PWR-001  
**Revision:** 0.1  
**Status:** Initial model

## Endurance Requirement

The minimum active communication endurance target is eight hours, with a ten-hour product objective.

## Load Domains

The power model shall separately account for:

- radio transmit;
- radio receive;
- RF synthesizer and timing;
- microphone bias and analog front end;
- ADC and DAC;
- processor;
- memory;
- status indicators;
- battery monitoring;
- regulation losses;
- leakage and shutdown current.

## Operating Cases

At minimum:

1. idle crew, listening only;
2. typical officiating speech;
3. one continuous dominant talker;
4. all six members speaking continuously;
5. poor-link retry condition;
6. coordinator role;
7. non-coordinator role;
8. low-temperature battery;
9. end-of-life battery capacity.

## Budget Method

For each domain:

`Energy = Current × Voltage × Time`

The endurance estimate shall include:

- converter efficiency;
- battery usable-capacity limit;
- aging reserve;
- cold-temperature reserve;
- manufacturing variation;
- warning reserve;
- update and setup energy.

## Initial Reserve Policy

The design shall not claim eight hours using nominal fresh-cell capacity alone.

The modeled release case should retain at least:

- 15% capacity aging reserve;
- 10% environmental and variation reserve;
- 10% low-battery warning and shutdown reserve.

## Required Measurements

Prototype current shall be measured with:

- time resolution sufficient to capture radio bursts;
- separate coordinator and member profiles;
- audio idle and worst-case audio processing;
- representative supply voltage;
- representative antenna match and output power.

## Executable Prototype 1 Budget

`tools/openref_power_budget.py` evaluates the explicit JSON assumptions in
`docs/power/prototype1-assumed-budget.json`. The initial 1,500 mAh single-cell
model allocates 235.5 mW average and applies the aging, environmental, and
warning reserves multiplicatively, leaving 68.85% usable nominal energy. It
estimates 16.2 hours and permits at most 382.1 mW average for the 10-hour target.

These are allocation results, not measurements or an endurance claim. The
executable model validates battery factors and loads with an explicit
`assumed`, `datasheet`, or `measured` evidence class. It reports
`release_ready: false` and names every unmeasured input until all release-case
inputs are measured. A positive arithmetic margin cannot close the gate.

The FGM230S RX and +14 dBm TX entries now use manufacturer typical values and
are labeled `datasheet`; a separate assumed allowance covers MCU scheduling and
security overhead. The model's useful early conclusion is that the combined
loads may rise by about 1.62 times before the 10-hour objective is lost. Each
non-measured domain must be
replaced with captured data and evidence metadata before Gate C can close.

Every input labeled `measured` must carry a structured record containing a
safe relative `artifact_file`, its SHA-256 digest, measurement method,
instrument identity, and UTC capture time. A measured label or filename alone
does not close the gate. Release evaluation also requires access to the actual
evidence directory so the model can re-hash every referenced artifact:

```text
python tools/openref_power_budget.py MEASURED-BUDGET.json \
  --evidence-root ARTIFACT-DIRECTORY --require-release
```

The output separately reports metadata completeness, artifact verification,
and final release readiness. Missing, escaped, or modified captures prevent
release even when the arithmetic endurance margin is positive.
