#ifndef OPENREF_NETWORK_EPOCH_FG23_H
#define OPENREF_NETWORK_EPOCH_FG23_H

#include <stdbool.h>
#include <stdint.h>

bool openref_network_epoch_fg23_load(uint32_t *persisted_epoch);

bool openref_network_epoch_fg23_advance(
    void *context,
    uint32_t current_epoch,
    uint32_t *persisted_next_epoch);

#endif
