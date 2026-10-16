// SPDX-License-Identifier: GPL-2.0-or-later
#include "hal.h"
extern void ducky_safety_early(void);
void __early_init(void) { ducky_safety_early(); NUC123_clock_init(); }
void boardInit(void) {}
#if !defined(PAL_NEW_INIT)
const PALConfig pal_default_config = {0};
#endif
