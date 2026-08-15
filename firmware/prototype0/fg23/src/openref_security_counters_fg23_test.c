#include <assert.h>
#include <stddef.h>
#include <stdint.h>

#include "openref_security_counters_fg23.h"

int main(void)
{
    uint32_t counter = 0u;
    openref_security_counter_context_t context = {
        .domain = OPENREF_COUNTER_ADMISSION,
    };
    assert(!openref_security_counter_fg23_load(
        OPENREF_COUNTER_ADMISSION, &counter));
    assert(!openref_security_counter_fg23_persist(&context, 1u));
    assert(!openref_security_counter_fg23_persist(NULL, 1u));
    return 0;
}
