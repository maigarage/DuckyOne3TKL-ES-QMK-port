#pragma once
#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>
#define MATRIX_ROWS 6
extern uint32_t now;
extern uint16_t keys;
extern uint32_t keymap_config;
static inline uint32_t timer_read32(void){return now;}
static inline uint32_t timer_elapsed32(uint32_t since){return now-since;}
static inline uint16_t matrix_get_row(unsigned r){return r==0?keys:0;}
void clear_keyboard(void);
void eeconfig_init(void);
void eeconfig_read_keymap(void *p);
void layer_clear(void);
void default_layer_set(uint32_t layer);

typedef struct {bool pressed;} keyrecord_t;
