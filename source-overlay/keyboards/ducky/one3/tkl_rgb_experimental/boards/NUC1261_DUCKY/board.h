// SPDX-License-Identifier: GPL-2.0-or-later
#pragma once
/* NUC123 CMSIS register view is reused only for common USB/GPIO/NVIC registers.
   Clock, multiplexing and matrix are NUC1261-specific. */
#define NUC123SD4AN0
#define NUC1261_DUCKY_EXPERIMENTAL
#define NUC123_HSECLK 12000000UL
#define BOARD_NAME "Ducky One3 TKL NUC1261 experimental"
#if !defined(_FROM_ASM_)
#ifdef __cplusplus
extern "C" {
#endif
void boardInit(void);
#ifdef __cplusplus
}
#endif
#endif
