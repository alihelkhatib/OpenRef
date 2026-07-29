# Prototype 0 Radio Abstraction

**Document ID:** OR-PRO-001  
**Revision:** 0.1  
**Status:** Initial implementation contract

## Purpose

Prevent Prototype 0 protocol logic from becoming permanently tied to a specific vendor radio API.

## Required Interface

```c
typedef struct {
    uint32_t frequency_hz;
    uint32_t bitrate_bps;
    int8_t tx_power_dbm;
    uint16_t preamble_symbols;
    uint8_t modulation_id;
    bool whitening_enabled;
    bool fec_enabled;
} openref_radio_profile_t;

typedef struct {
    uint64_t local_timestamp_us;
    int16_t rssi_dbm;
    int8_t lqi;
    bool crc_ok;
    uint16_t length;
} openref_rx_metadata_t;

typedef enum {
    OPENREF_RADIO_OK = 0,
    OPENREF_RADIO_BUSY,
    OPENREF_RADIO_TIMEOUT,
    OPENREF_RADIO_INVALID,
    OPENREF_RADIO_HW_FAULT
} openref_radio_result_t;
```

Minimum functions:

```c
openref_radio_result_t openref_radio_init(
    const openref_radio_profile_t *profile);

openref_radio_result_t openref_radio_schedule_tx(
    uint64_t timestamp_us,
    const uint8_t *payload,
    uint16_t length);

openref_radio_result_t openref_radio_start_rx(
    uint64_t start_timestamp_us,
    uint32_t duration_us);

openref_radio_result_t openref_radio_read(
    uint8_t *payload,
    uint16_t capacity,
    openref_rx_metadata_t *metadata);

uint64_t openref_radio_time_us(void);

openref_radio_result_t openref_radio_cancel(void);

openref_radio_result_t openref_radio_get_faults(
    uint32_t *fault_bitmap);
```

## Behavioral Requirements

- timestamps shall be monotonic within a boot session;
- scheduled transmit shall report whether the deadline was accepted;
- received packets shall include local arrival timing and signal metadata;
- queues shall be bounded;
- cancellation behavior shall be deterministic;
- radio faults shall not silently reset crew protocol state;
- vendor callback context shall not execute application protocol logic directly.

## Vendor Adaptation

Initial adapters:

```text
firmware/platform/ti_cc1352p7/openref_radio_ti.c
firmware/platform/silabs_fg23/openref_radio_silabs.c
```

The network layer shall include neither TI nor Silicon Labs header files.

## Prototype Instrumentation

Development builds shall expose GPIO markers for:

- audio-frame ready;
- packet queued;
- transmit start;
- transmit complete;
- receive sync detected;
- receive complete;
- playback start;
- coordinator transition.

These markers enable oscilloscope and logic-analyzer latency measurements independent of software logs.
