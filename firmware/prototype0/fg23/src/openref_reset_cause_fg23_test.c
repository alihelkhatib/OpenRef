#include <assert.h>
#include <string.h>

#include "openref_reset_cause_fg23.h"

int main(void)
{
    uint32_t flags = openref_reset_cause_fg23_classify(
        OPENREF_FG23_RESET_RAW_WDOG0 | OPENREF_FG23_RESET_RAW_BROWNOUT);
    assert((flags & OPENREF_RESET_CAUSE_WATCHDOG) != 0u);
    assert((flags & OPENREF_RESET_CAUSE_BROWNOUT) != 0u);
    assert((flags & OPENREF_RESET_CAUSE_UNKNOWN) == 0u);
    assert(openref_reset_cause_fg23_classify(0u) == OPENREF_RESET_CAUSE_UNKNOWN);
    assert((openref_reset_cause_fg23_classify(UINT32_C(0x00100000)) &
            OPENREF_RESET_CAUSE_UNKNOWN) != 0u);

    openref_reset_cause_fg23_t cause;
    memset(&cause, 0, sizeof(cause));
    assert(!openref_reset_cause_fg23_capture(&cause));
    assert(!cause.captured);
    return 0;
}
