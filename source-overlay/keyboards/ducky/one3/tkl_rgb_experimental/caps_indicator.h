// SPDX-License-Identifier: GPL-2.0-or-later
#pragma once
#include "quantum.h"
void ducky_caps_set(bool enabled);
void ducky_caps_task(void);
void ducky_rgb_suspend(void);
void ducky_rgb_resume(void);
bool ducky_rgb_process(uint16_t keycode,keyrecord_t *record);

void ducky_scroll_set(bool enabled);
void ducky_mouse_set(bool enabled);
