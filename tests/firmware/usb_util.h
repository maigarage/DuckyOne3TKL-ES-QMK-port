#pragma once
#include <stdbool.h>
static inline bool usb_connected_state(void) {return *(volatile unsigned char *)0x20007005==0;}
