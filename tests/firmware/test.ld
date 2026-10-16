ENTRY(ducky_caps_task)
SECTIONS {
 . = 0x1000;
 .text : { *(.text*) *(.rodata*) }
 . = 0x20000000;
 .data : { *(.data*) }
 .bss (NOLOAD) : { *(.bss*) *(COMMON) }
 /DISCARD/ : { *(.ARM.exidx*) *(.ARM.extab*) *(.comment*) }
}
