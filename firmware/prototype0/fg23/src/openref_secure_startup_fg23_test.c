#include <assert.h>

#include "openref_secure_startup_fg23.h"

int main(void)
{
    openref_secure_startup_t startup;
    assert(!openref_secure_startup_fg23_init(&startup));
    assert(!startup.initialized);
    return 0;
}
