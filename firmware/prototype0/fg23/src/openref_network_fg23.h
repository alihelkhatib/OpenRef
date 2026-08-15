#ifndef OPENREF_NETWORK_FG23_H
#define OPENREF_NETWORK_FG23_H

#include <stdbool.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

void openref_network_fg23_init(void);
void openref_network_fg23_process(void);

bool openref_network_fg23_configure_security(
    uint32_t crew_session_id,
    uint32_t boot_counter,
    uint32_t initial_packet_counter,
    const uint8_t crew_session_key[16]);

bool openref_network_fg23_clear_security(void);

#ifdef __cplusplus
}
#endif

#endif
