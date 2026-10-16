/* SPDX-License-Identifier: GPL-2.0-or-later */
.syntax unified
.cpu cortex-m0
.thumb
.section .text.ducky_safety_cutoff,"ax",%progbits
.global ducky_safety_cutoff
.type ducky_safety_cutoff,%function
.thumb_func
ducky_safety_cutoff:
    /* Stackless, no library/RTOS calls; drop all rows before stopping clocks. */
    movs r1, #0
    ldr r0, =0x50004280
    str r1, [r0, #0x18]
    str r1, [r0, #0x14]
    ldr r0, =0x500042c0
    str r1, [r0, #0x1c]
    str r1, [r0, #0x3c]
    str r1, [r0, #0x38]
    str r1, [r0, #0x34]
    ldr r0, =0x50004348
    str r1, [r0]
    movs r1, #1
    ldr r0, =0x5000429c
    str r1, [r0]
    bx lr
.size ducky_safety_cutoff, .-ducky_safety_cutoff
.ltorg
.section .text.ducky_safety_halt,"ax",%progbits
.global HardFault_Handler
.global _unhandled_exception
.global Vector44
.global ducky_safety_halt
.type ducky_safety_halt,%function
.thumb_func
ducky_safety_halt:
    cpsid i
    bl ducky_safety_cutoff
    /* WDT, when running, resets independently. Before RGB init, stay dark. */
1:  b 1b
.size ducky_safety_halt, .-ducky_safety_halt
.thumb_set HardFault_Handler, ducky_safety_halt
.thumb_set _unhandled_exception, ducky_safety_halt
.thumb_set Vector44, ducky_safety_halt
.section .note.GNU-stack,"",%progbits
