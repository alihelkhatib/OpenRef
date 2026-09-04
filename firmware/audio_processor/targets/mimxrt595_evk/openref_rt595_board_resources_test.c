#include "openref_rt595_board_resources.h"
#include <assert.h>
#include <stdio.h>
int main(void)
{
    assert(OPENREF_RT595_FLEXCOMM_DEBUG == 0u);
    assert(OPENREF_RT595_FLEXCOMM_I2S_TX == 3u);
    assert(OPENREF_RT595_FLEXCOMM_SPI == 5u);
    assert(OPENREF_RT595_SPI_SCK_PORT == 1u && OPENREF_RT595_SPI_SCK_PIN == 3u);
    assert(OPENREF_RT595_SPI_CIPO_PIN == 4u && OPENREF_RT595_SPI_COPI_PIN == 5u);
    assert(OPENREF_RT595_SPI_SSEL0_PIN == 6u);
    puts("openref_rt595_board_resources_test: PASS");
    return 0;
}
