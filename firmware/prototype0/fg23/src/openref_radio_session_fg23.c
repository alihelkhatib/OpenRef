#include "openref_radio_session_fg23.h"

#include "openref_network_fg23.h"

static bool provision(void *context, uint32_t crew_session_id,
    uint32_t boot_counter, uint32_t initial_packet_counter,
    const uint8_t key[OPENREF_CREW_SESSION_KEY_BYTES])
{
    (void)context;
    return openref_network_fg23_configure_security(
        crew_session_id, boot_counter, initial_packet_counter, key);
}

static bool disable(void *context)
{
    (void)context;
    return openref_network_fg23_clear_security();
}

openref_radio_session_backend_t openref_radio_session_fg23_backend(void)
{
    openref_radio_session_backend_t backend = {
        .provision = provision,
        .disable = disable,
    };
    return backend;
}
