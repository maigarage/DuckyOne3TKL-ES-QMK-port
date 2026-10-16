// SPDX-License-Identifier: GPL-2.0-or-later
#include "hal.h"
#if OSAL_ST_MODE != OSAL_ST_MODE_PERIODIC
#error "NUC1261 prototype requires periodic SysTick"
#endif
OSAL_IRQ_HANDLER(SysTick_Handler) {
 OSAL_IRQ_PROLOGUE(); osalSysLockFromISR(); osalOsTimerHandlerI(); osalSysUnlockFromISR(); OSAL_IRQ_EPILOGUE();
}
void st_lld_init(void) {
 SysTick->LOAD=48000000UL/OSAL_ST_FREQUENCY-1;
 SysTick->VAL=0;
 SysTick->CTRL=SysTick_CTRL_CLKSOURCE_Msk|SysTick_CTRL_ENABLE_Msk|SysTick_CTRL_TICKINT_Msk;
 nvicSetSystemHandlerPriority(HANDLER_SYSTICK,NUC123_ST_IRQ_PRIORITY);
}
