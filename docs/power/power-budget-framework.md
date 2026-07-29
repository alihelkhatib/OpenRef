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
