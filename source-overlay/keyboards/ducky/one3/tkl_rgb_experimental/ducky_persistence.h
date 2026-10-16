// SPDX-License-Identifier: GPL-2.0-or-later
#pragma once
#include <stdbool.h>
#include <stdint.h>
void ducky_settings_init(void);
void ducky_settings_task(void);
void ducky_settings_command(uint8_t *data,uint8_t length);
void ducky_rgb_export(uint8_t *data);
bool ducky_rgb_import(const uint8_t *data);
void ducky_rgb_defaults(void);

bool ducky_rgb_editing(void);
