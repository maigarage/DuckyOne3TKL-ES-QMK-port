# SPDX-License-Identifier: GPL-2.0-or-later
MCU_FAMILY = NUMICRO
MCU_SERIES = NUC1261
MCU = cortex-m0
ARMV = 6
MCU_STARTUP = NUC123
MCU_LDSCRIPT = NUC1261_test
BOARD = NUC1261_DUCKY
BOOTLOADER = custom
CUSTOM_MATRIX = lite
SRC += matrix.c caps_indicator.c
EEPROM_DRIVER = custom
VIA_ENABLE = yes
LTO_ENABLE = yes

MOUSEKEY_ENABLE = yes
SRC += ducky_stock.c ducky_stock_blob.S ducky_mouse.c

SRC += ducky_safety.c ducky_safety_asm.S

SRC += ducky_store.c ducky_flash.c ducky_persistence.c

# No stack trampolines; declare ELF stack policy even for legacy newlib objects.
LDFLAGS += -Wl,-z,noexecstack
