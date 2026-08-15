#include <assert.h>
#include <stddef.h>

#include "openref_secure_startup.h"

typedef struct {
    uint32_t counter;
    bool found;
    bool radio_disabled;
    uint32_t provisioned_boot;
} probe_t;

static bool read_counter(void *context, uint32_t *value, bool *found)
{
    probe_t *probe = context;
    *value = probe->counter;
    *found = probe->found;
    return true;
}

static bool write_counter(void *context, uint32_t value)
{
    probe_t *probe = context;
    probe->counter = value;
    probe->found = true;
    return true;
}

static bool provision(void *context, uint32_t session_id,
    uint32_t boot_counter, uint32_t packet_counter, const uint8_t *key)
{
    probe_t *probe = context;
    (void)session_id;
    (void)packet_counter;
    (void)key;
    probe->provisioned_boot = boot_counter;
    return true;
}

static bool disable(void *context)
{
    ((probe_t *)context)->radio_disabled = true;
    return true;
}

int main(void)
{
    probe_t probe = {.counter = 4u, .found = true};
    openref_radio_session_backend_t radio = {provision, disable, &probe};
    openref_secure_startup_t startup;
    assert(openref_secure_startup_init(
        &startup, read_counter, write_counter, &probe, radio));
    assert(startup.initialized && startup.active_boot_counter == 5u);
    assert(probe.counter == 5u && probe.radio_disabled);
    openref_crew_key_backend_t crew =
        openref_secure_startup_crew_key_backend(&startup);
    uint8_t key[OPENREF_CREW_SESSION_KEY_BYTES] = {1u};
    assert(crew.install(crew.context, 7u, key));
    assert(probe.provisioned_boot == 5u);

    probe.counter = UINT32_MAX;
    probe.found = true;
    assert(!openref_secure_startup_init(
        &startup, read_counter, write_counter, &probe, radio));
    crew = openref_secure_startup_crew_key_backend(&startup);
    assert(crew.install == NULL && crew.erase == NULL);
    return 0;
}
