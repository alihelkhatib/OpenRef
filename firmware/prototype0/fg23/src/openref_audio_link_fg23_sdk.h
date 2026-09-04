#ifndef OPENREF_AUDIO_LINK_FG23_SDK_H
#define OPENREF_AUDIO_LINK_FG23_SDK_H
#include <stdbool.h>
#include "openref_audio_link_fg23.h"
bool openref_audio_fg23_sdk_init(openref_audio_fg23_t *adapter);
void openref_audio_fg23_sdk_process(void);
#endif
