#include <assert.h>
#include <stddef.h>

#include "openref_radio_session_fg23.h"

int main(void)
{
    openref_radio_session_backend_t backend =
        openref_radio_session_fg23_backend();
    uint8_t key[OPENREF_CREW_SESSION_KEY_BYTES] = {1u};
    assert(backend.provision != NULL && backend.disable != NULL);
    assert(!backend.provision(backend.context, 1u, 1u, 1u, key));
    assert(!backend.disable(backend.context));
    return 0;
}
