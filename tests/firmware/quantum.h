#pragma once
#include <stdint.h>
#include <stdbool.h>
typedef enum {TICK_EVENT=0,KEY_EVENT=1} keyevent_type_t;
typedef struct { struct {struct {uint8_t col,row;} key; uint16_t time; keyevent_type_t type; bool pressed;} event;} keyrecord_t;
static inline uint32_t timer_read32(void) { return *(volatile uint32_t *)0x20007000; }
static inline uint16_t timer_read(void) { return timer_read32(); }
#include "keycodes.h"
#ifndef MO
#define MO(x) (0x5220+(x))
#endif
#define MOD_MASK_ALT 0x44
#ifndef VALIDATION_MOUSE
static inline uint8_t get_mods(void) {return *(volatile uint8_t *)0x20007004;}
#endif
