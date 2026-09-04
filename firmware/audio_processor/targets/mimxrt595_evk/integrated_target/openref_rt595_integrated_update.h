#ifndef OPENREF_RT595_INTEGRATED_UPDATE_H
#define OPENREF_RT595_INTEGRATED_UPDATE_H

#include <stdint.h>
#include "openref_rt595_update_delivery.h"

/* Entry points for an authenticated/authorized command demultiplexer.  Raw
 * unauthenticated processor-link traffic must never call this API. */
openref_rt595_update_delivery_result_t openref_rt595_integrated_update_begin(
    uint32_t session_id, uint8_t target_slot,
    const uint8_t manifest[OPENREF_UPDATE_MANIFEST_BYTES], uint32_t now_us);
openref_rt595_update_delivery_result_t openref_rt595_integrated_update_chunk(
    uint32_t session_id, uint32_t sequence, uint32_t offset,
    const uint8_t *data, uint16_t length, uint32_t now_us);
openref_rt595_update_delivery_result_t openref_rt595_integrated_update_finish(
    uint32_t session_id, uint32_t sequence, uint32_t now_us);
void openref_rt595_integrated_update_reset(void);

#endif
