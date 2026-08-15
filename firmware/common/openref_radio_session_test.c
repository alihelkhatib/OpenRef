#include <assert.h>
#include <string.h>

#include "openref_radio_session.h"

typedef struct {
    uint32_t session_id;
    uint32_t boot_counter;
    uint32_t packet_counter;
    uint8_t key[OPENREF_CREW_SESSION_KEY_BYTES];
    uint32_t disable_calls;
    bool provision_ok;
    bool disable_ok;
} probe_t;

static bool provision(void *context, uint32_t session_id,
    uint32_t boot_counter, uint32_t packet_counter, const uint8_t *key)
{
    probe_t *probe = context;
    probe->session_id = session_id;
    probe->boot_counter = boot_counter;
    probe->packet_counter = packet_counter;
    memcpy(probe->key, key, sizeof(probe->key));
    return probe->provision_ok;
}

static bool disable(void *context)
{
    probe_t *probe = context;
    probe->disable_calls++;
    return probe->disable_ok;
}

int main(void)
{
    probe_t probe = {.provision_ok = true, .disable_ok = true};
    openref_radio_session_backend_t target = {provision, disable, &probe};
    openref_radio_session_t radio;
    assert(openref_radio_session_init(&radio, target, 9u));
    assert(probe.disable_calls == 1u);
    openref_crew_key_backend_t crew =
        openref_radio_session_crew_key_backend(&radio);
    uint8_t key[OPENREF_CREW_SESSION_KEY_BYTES];
    memset(key, 0x5a, sizeof(key));
    assert(crew.install(crew.context, 22u, key));
    assert(radio.active && radio.active_session_id == 22u);
    assert(probe.boot_counter == 9u && probe.packet_counter == 1u);
    assert(memcmp(probe.key, key, sizeof(key)) == 0);
    assert(!crew.install(crew.context, 23u, key));
    assert(radio.failures == 1u);
    assert(crew.erase(crew.context));
    assert(!radio.active && probe.disable_calls == 2u);

    probe.provision_ok = false;
    assert(!crew.install(crew.context, 23u, key));
    assert(!radio.active && radio.failures == 2u);
    probe.disable_ok = false;
    assert(!crew.erase(crew.context));
    assert(!radio.active && radio.failures == 3u);
    assert(!openref_radio_session_init(&radio, target, 0u));
    return 0;
}
