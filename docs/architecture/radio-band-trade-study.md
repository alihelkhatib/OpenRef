# Radio Band Trade Study

**Document ID:** OR-ARC-008  
**Revision:** 0.1  
**Status:** Preliminary; prototype evidence required

## Decision Context

OpenRef requires reliable, low-latency, full-duplex voice for at least six body-worn users without phones, infrastructure, or cloud services.

The first architecture comparison is between:

- sub-GHz operation in the U.S. 902–928 MHz ISM band;
- 2.4 GHz ISM operation;
- a dual-band or split-control/data architecture.

## Evaluation Criteria

| Criterion | Importance |
|---|---|
| Body-worn propagation | Critical |
| Available channel capacity | Critical |
| Deterministic latency | Critical |
| Coexistence behavior | Critical |
| Antenna size and efficiency | High |
| Module and silicon availability | High |
| Power consumption | High |
| U.S. regulatory path | High |
| Global portability | Medium |
| Cost | Medium |

## 902–928 MHz

### Strengths

- generally more favorable propagation around people and field obstructions;
- potentially greater useful range for a given link margin;
- lower path loss than 2.4 GHz at equal geometry;
- less direct competition with conventional Wi-Fi and Bluetooth traffic.

### Weaknesses

- larger efficient antenna requirement;
- less total bandwidth than 2.4 GHz alternatives;
- fewer high-throughput commodity voice-networking platforms;
- regional regulatory differences reduce global portability;
- body placement can still strongly detune or shadow the antenna.

## 2.4 GHz

### Strengths

- broad silicon and module ecosystem;
- smaller practical antennas;
- higher available data rates;
- mature coexistence mechanisms in many radios;
- simpler path toward global variants.

### Weaknesses

- heavy Wi-Fi and Bluetooth occupancy;
- greater body attenuation and shadowing;
- potentially shorter reliable range at equivalent power;
- coexistence must be proven in tournament environments.

## Dual-Band or Split Architecture

Possible forms include:

- sub-GHz audio with 2.4 GHz maintenance or setup;
- 2.4 GHz primary audio with sub-GHz emergency control;
- selectable regional radio modules.

This approach is not preferred for Version 1 unless a single-band design fails a mandatory requirement because it increases:

- component count;
- firmware complexity;
- antenna interactions;
- certification scope;
- test burden;
- cost and power consumption.

## Preliminary Direction

Both 902–928 MHz and 2.4 GHz shall remain active candidates through proof-of-concept testing.

No band shall be selected solely from theoretical range. The down-selection requires measured evidence for:

- six-user airtime;
- one-way latency distribution;
- body-worn field range;
- coexistence;
- current consumption;
- antenna sensitivity to orientation;
- nearby independent crews.

## Down-Selection Gate

A candidate must demonstrate:

1. six simultaneous source streams with required margin;
2. acceptable operation in representative Wi-Fi and Bluetooth congestion;
3. body-worn coverage across a full field;
4. no architecture-breaking antenna requirement;
5. projected eight-hour endurance;
6. a practical U.S. authorization path.
