#include <assert.h>
#include <stddef.h>
#include <stdint.h>

#include "openref_network_epoch_fg23.h"

int main(void)
{
    uint32_t next = 0u;
    assert(!openref_network_epoch_fg23_load(&next));
    assert(!openref_network_epoch_fg23_advance(NULL, 0u, &next));
    assert(next == 0u);
    return 0;
}
