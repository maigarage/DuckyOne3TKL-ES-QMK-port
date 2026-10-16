// SPDX-License-Identifier: GPL-2.0-or-later
/* Standalone RGB harness only; linked-firmware tests use the real modules. */
#include <stdbool.h>
#include <stdint.h>
bool ducky_mouse_enabled(void){return *(volatile uint8_t *)0x20007006;}
void ducky_mouse_restore(bool on){*(volatile uint8_t *)0x20007006=on;}
void ducky_settings_command(uint8_t *data,uint8_t length){(void)data;(void)length;}
