# USB shutdown and RGB recovery — test10.4

Historical investigation. For the current release, timing policy and physical
acceptance steps, see [BIOS_USB.md](BIOS_USB.md).

## Observed failure

The user reported that turning the PC off caused one lighting blink. After the
next PC startup, typing and VIA still worked, but both RGB and the independent
indicators stayed dark. Removing and reconnecting USB power restored lighting.
The captured test10.3 diagnostic was:

```json
{"RSTSTS":"0x6c","BODCTL":"0x386","PORCTL":"0x0","WDT_CTL":"0x4",
 "CLKSEL0":"0x3c","CLKSEL1":"0x3377770f","CLKDIV0":"0x10","RGB_STATUS":"0x5a01"}
```

The RGB status confirms a latched fault with scanning stopped and ceiling 90.
The watchdog reset flag is present in both reset status and WDT control. Low
voltage reset is also flagged. Reset flags may accumulate; this capture does
not establish their order or prove that the USB scheduling gap was the only
physical trigger. The reset flags are not cleared by this update.

## Confirmed software gap and correction

In test10.3, the scan IRQ blanked rows and returned when USB was inactive. The
watchdog was stopped later by foreground suspension code. While foreground
processing was delayed, the scanner could no longer make progress and the
watchdog could expire. On reboot, the existing watchdog-reset guard deliberately
left the shared RGB/indicator scanner disabled. VIA changes did not clear it.

In test10.4 the scan IRQ itself quiesces the RGB hardware when USB becomes
inactive: all seven row gates off, PC7 output disabled, timer and its IRQ stopped,
gray-clock output off, then RGB watchdog stopped. USB is checked both before and
after serial transfer because higher-priority USB interrupts can preempt it.
Engine/editor cleanup remains in foreground code. Once USB is configured again,
the foreground initializes the output and restarts its watchdog and scanner.
Duplicate wake notifications leave an already running scanner alone.

The watchdog stop routine is bounded and uses registers only; it does not call
RTOS, HID, allocation or vendor-engine routines. It executes after outputs are
disabled. During settings flash writes RGB already has `running=false`, so the
scan IRQ cannot disable the watchdog protecting that transaction.

Real heartbeat expiry, active-USB scan overrun, invalid state, failed watchdog
startup and watchdog/CPU-lockup reset flags still latch dark. There is no blanket
automatic recovery or unconditional clearing of reset flags. No flash writes,
voltage thresholds, LED current settings or bootloader behavior were added.

## Does original Ducky firmware handle this?

**Yes: original TKL RGB 1.16 has explicit USB suspend/resume paths.** Evidence
comes from the exact APROM extracted by this project's verified official-updater
download. SHA-256:
`e04458f82c1a14baa1b77fd4d63c1b9046a93fd2ed6efe5fc778fbbf87d72c59`.

| Original APROM location | Observed behavior |
| --- | --- |
| USB IRQ vector / handler `0xa154` | Handles USB bus reset, suspend and resume bits. |
| `0xa1ae–0xa1ba` | Sets suspend byte `0x20002e41` to 1 and disables the USB PHY bit. |
| `0xa1c2–0xa1ce` | Enables USB/PHY and clears the suspend byte on resume. |
| Foreground dispatcher `0x33f4`, branches `0x3416–0x3440` | Detects suspension/resumption and calls distinct transition routines. |
| Suspend routine `0x3ae4` | Stops/reconfigures output peripherals and clears PC output latches. |
| Resume routine `0x3b98` | Reconfigures/restarts the output path. |

`tests/firmware/test_stock_usb.py` executes the actual USB interrupt instructions
and foreground branch selection in an ARM emulator, confirming the suspend byte
and calls to the two transition routines. The hardware transition routines and
the associated `0x31b8` call are intercepted, so this test is control-flow
evidence, not electrical validation of original firmware. No claim is made that
the original uses the same watchdog policy as this port.

Our port uses its own QMK/ChibiOS USB lifecycle and RGB hardware scanner; relocating
the original effect calculations does not import Ducky's complete power handling.
The original event handlers are therefore reference evidence, not code copied
into the new recovery path.

## Diagnostics and physical acceptance

Rebuild and flash test10.4 using the complete source package. Disconnect USB power
once before upgrading if test10.3 is currently latched dark; never disconnect
during flashing. The storage schema and manual Save policy are unchanged.

1. Confirm normal typing, Full Backlit and active Caps/Scroll/mouse indicators.
2. Shut down the PC normally, leave the cable connected, then start the PC again.
3. Check RGB, indicators and VIA controls. Repeat at least five times and also
   test ordinary sleep/wake. Do not press Save during these lifecycle checks.
4. Close VIA and run `tools/diagnostics.py` with the workspace runtime Python.
   Expect `rgb_fault=false` and `rgb_running=true` after USB is configured.
5. `usb_pause_count` counts IRQ-handled USB pauses in the current boot, not all
   suspensions. Foreground suspension may win the race, and power loss resets the
   counter, so zero alone does not mean the fix failed.
6. If it fails, capture diagnostics before unplugging. The new
   `rgb_fault_reason_code` distinguishes the startup reset guard, heartbeat,
   scan overrun and invalid state. Capture a healthy-start report as well.

Windows PowerShell example (adjust source/workspace paths):

```powershell
& "C:\DuckyOne3\runtime\Scripts\python.exe" "C:\DuckySource\ducky-one3-tkl-qmk\tools\diagnostics.py"
```

Ubuntu example:

```bash
"$HOME/DuckyOne3/runtime/bin/python" "$HOME/ducky-one3-tkl-qmk/tools/diagnostics.py"
```

Diagnostics only reads VIA values. It cannot clear a fault or write settings.
Software regression tests do not reproduce actual host-power rail behavior,
oscillator timing, USB interrupt latency or repeated physical PC shutdowns.
