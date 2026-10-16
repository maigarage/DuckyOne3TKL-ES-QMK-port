// SPDX-License-Identifier: GPL-2.0-or-later
#pragma once
#include <stdint.h>
#include <stdbool.h>
void ducky_safety_early(void) __attribute__((noinline));
void ducky_safety_cutoff(void);
void ducky_safety_halt(void) __attribute__((noreturn));
bool ducky_watchdog_start(void) __attribute__((noinline));
void ducky_watchdog_stop(void) __attribute__((noinline));
void ducky_watchdog_feed(void);
uint32_t ducky_reg_unlock(void);
void ducky_reg_lock(uint32_t state);
