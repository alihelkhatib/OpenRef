#include <assert.h>

#include "openref_device_record_store_fg23.h"

int main(void)
{
    openref_config_backend_t backend =
        openref_device_record_store_fg23_backend();
    uint8_t record[OPENREF_CONFIG_SLOT_BYTES] = {0};
    assert(backend.read_slot != 0 && backend.write_slot != 0);
    assert(!backend.read_slot(backend.context, 0u, record));
    assert(!backend.write_slot(backend.context, 0u, record));
    assert(!backend.read_slot(backend.context, 2u, record));
    return 0;
}
