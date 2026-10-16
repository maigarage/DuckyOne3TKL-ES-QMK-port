// SPDX-License-Identifier: GPL-2.0-or-later
#pragma once
#include <stdbool.h>
#include <stdint.h>
#define DUCKY_STORE_BASE 0x1e000u
#define DUCKY_STORE_BANK_SIZE 4096u
#define DUCKY_STORE_PAGE_SIZE 2048u
#define DUCKY_EEPROM_SIZE 2048u
#define DUCKY_RGB_SIZE 416u
#define DUCKY_STORE_PAYLOAD (DUCKY_EEPROM_SIZE + DUCKY_RGB_SIZE)
#define DUCKY_STORE_MAGIC 0x31534b44u
#define DUCKY_STORE_SCHEMA 0x000a0001u
/* Flash backend is restricted to this partition, including in its RAM routine. */
uint32_t ducky_flash_read(uint32_t address);
bool ducky_flash_program(uint32_t address, uint32_t value);
bool ducky_flash_erase(uint32_t address);
uint32_t ducky_store_source_word(uint32_t offset);
void ducky_store_restore_word(uint32_t offset, uint32_t value);
int ducky_store_load(void);
int ducky_store_latest(void);
/* 1 = committed, 2 = already identical, -1 = I/O failure, -2 = unknown region */
int ducky_store_save(void);
