// SPDX-License-Identifier: GPL-2.0-or-later
#pragma once
#include "quantum.h"
bool ducky_mouse_process(uint16_t keycode,keyrecord_t *record);
void ducky_mouse_release(void);

bool ducky_mouse_enabled(void);
void ducky_mouse_restore(bool on);
