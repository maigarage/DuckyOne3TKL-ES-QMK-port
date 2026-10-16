#pragma once
#define VALIDATION_MOUSE
#include "../quantum.h"
#undef QK_KB_0
#undef QK_KB_5
#undef QK_KB_9
#define MATRIX_ROWS 6
#define MATRIX_COLS 16
#define MOD_MASK_ALT 0x44
uint8_t get_mods(void);
bool layer_state_is(uint8_t layer);
