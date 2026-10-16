// SPDX-License-Identifier: GPL-2.0-or-later
#pragma once
#define EEPROM_SIZE 2048
#define DYNAMIC_KEYMAP_EEPROM_MAX_ADDR 2047
#define DYNAMIC_KEYMAP_LAYER_COUNT 4
#define USB_POLLING_INTERVAL_MS 1
#define DEBOUNCE 5

#define CPU_CLOCK 48000000UL

/* The NuMicro driver allocates separate hardware slots per direction. */
#define USB_ENDPOINTS_ARE_REORDERABLE
