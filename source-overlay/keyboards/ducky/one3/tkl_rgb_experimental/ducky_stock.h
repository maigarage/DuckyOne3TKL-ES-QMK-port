// SPDX-License-Identifier: GPL-2.0-or-later
#pragma once
#include <stdint.h>
#include <stdbool.h>
void ducky_stock_init(void);
void ducky_stock_mode(uint8_t mode);
void ducky_stock_step(void); /* one completed 7-bank frame, nominally 7 ms */
void ducky_stock_key(uint8_t row,uint8_t col,bool pressed);
void ducky_stock_channels(const uint8_t channels[3]);
void ducky_stock_speed(uint8_t value);
uint8_t ducky_stock_get_speed(void);
uint16_t ducky_stock_pixel(uint8_t row,uint8_t col,uint8_t channel);
uint16_t ducky_stock_palette(uint8_t row,uint8_t col,uint8_t channel);
extern const uint16_t ducky_stock_lut[11];

void ducky_stock_release(void);

void ducky_stock_export_speeds(uint8_t values[12]);
void ducky_stock_import_speeds(const uint8_t values[12]);
