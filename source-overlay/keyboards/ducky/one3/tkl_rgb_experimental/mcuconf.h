// SPDX-License-Identifier: GPL-2.0-or-later
#pragma once
#define NUC123_MCUCONF
#define NUC1261_EXPERIMENTAL
#define NUC123_HCLK 48000000UL
#define NUC123_HSE_ENABLED FALSE
#define NUC123_PLL_ENABLED FALSE
#define NUC123_USB_USE_USB1 TRUE
#define NUC123_SERIAL_USE_UART0 FALSE

#define NUC123_USB_WORKAROUND TRUE
/* Keep USB and 10 kHz SysTick service above the RGB transfer IRQ (priority 3). */
#define NUC123_USB_IRQ_PRIORITY 2
#define NUC123_ST_IRQ_PRIORITY 2
