#ifndef OPENREF_RADIO_H
#define OPENREF_RADIO_H

#include <stdbool.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

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

openref_radio_result_t openref_radio_get_faults(uint32_t *fault_bitmap);

#ifdef __cplusplus
}
#endif

#endif
