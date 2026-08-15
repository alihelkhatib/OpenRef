#include <assert.h>
#include <stdint.h>

#include "openref_boot_counter_fg23.h"

int main(void)
{
    uint32_t counter = 0u;
    assert(!openref_boot_counter_fg23_advance(&counter));
    return 0;
}
