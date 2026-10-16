// SPDX-License-Identifier: GPL-2.0-or-later
#include "ducky_mouse.h"
#include "caps_indicator.h"
#include "mousekey.h"
static bool enabled;
/* Ownership survives mode changes, so release cannot leak a key-up or stick a button. */
static uint16_t captured[MATRIX_ROWS][MATRIX_COLS];
static uint16_t translate(uint16_t keycode) {
    switch(keycode) {
        case KC_HOME:return MS_UP; case KC_END:return MS_DOWN;
        case KC_DEL:return MS_LEFT; case KC_PGDN:return MS_RGHT;
        case KC_INS:return MS_BTN1; case KC_PGUP:return MS_BTN2;
        case KC_PSCR:return MS_WHLD; case KC_PAUS:return MS_WHLU;
        default:return 0;
    }
}
void ducky_mouse_release(void) {
    for(unsigned r=0;r<MATRIX_ROWS;r++) for(unsigned c=0;c<MATRIX_COLS;c++)
        if(captured[r][c] && captured[r][c]!=0xffff) mousekey_off(captured[r][c]);
    mousekey_send();
}
bool ducky_mouse_process(uint16_t keycode,keyrecord_t *record) {
    unsigned r=record->event.key.row,c=record->event.key.col;
    if(r>=MATRIX_ROWS || c>=MATRIX_COLS) return true;
    if(!record->event.pressed && captured[r][c]) {
        if(captured[r][c]!=0xffff) {mousekey_off(captured[r][c]);mousekey_send();}
        captured[r][c]=0; return false;
    }
    /* Fn + Alt + ScrLk, same documented chord as the stock TKL.
     * QK_KB_10 allows the same toggle to be assigned through VIA Any. */
    bool toggle=keycode==QK_KB_10 || (keycode==KC_SCRL && layer_state_is(1) && (get_mods()&MOD_MASK_ALT));
    if(toggle) {
        if(record->event.pressed) {
            ducky_mouse_release(); enabled=!enabled;
            ducky_mouse_set(enabled); captured[r][c]=0xffff;
        }
        return false;
    }
    if(enabled && record->event.pressed) {
        uint16_t code=translate(keycode);
        if(code) {captured[r][c]=code;mousekey_on(code);mousekey_send();return false;}
    }
    return true;
}

bool ducky_mouse_enabled(void) {return enabled;}
void ducky_mouse_restore(bool on) {ducky_mouse_release();enabled=on;ducky_mouse_set(on);}
