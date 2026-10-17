# BIOS and USB startup — test10.5

## What the latest report establishes

The reported `RSTSTS=0x64`, fault reason 1, `scan_sequence=0` and
`usb_pause_count=0` show that the RGB startup guard refused to start after seeing
a watchdog reset flag. They do not identify the instruction that originally
stalled. Reset flags can accumulate, and the earlier RAM fault reason is lost
across reset. No voltage, current or temperature was measured.

Source inspection identified a concrete timing conflict: the pinned QMK HID
transport permits a finite 100 ms queue wait, while the RGB foreground heartbeat
faults after 50 scan periods. Such a wait can occur while USB still reports
configured/active. The test10.4 inactive-USB fix does not cover that case.
This is a plausible contributor to the reported BIOS behavior, not a physical
reproduction of its original cause.

## Bounded USB waits

The finite HID send path now declares a temporary wait to the RGB controller.
One declaration surrounds the entire send/retry loop; retries and nested calls
cannot renew it. Infinite waits receive no exemption.

- Outside a declared wait, the existing heartbeat still faults on scan 51.
- During a declared wait, a separate counter permits at most 125 successful
  scan periods (nominally about 125 ms). Scan 126 latches fault reason 9.
- Only a completed scan with valid state, active USB, no overrun and normal
  blank/shift/gate sequencing may feed the hardware watchdog during that wait.
- The hardware watchdog configuration remains unchanged: independent LIRC,
  nominal 1024 ticks, about 102.4 ms at nominal 10 kHz. Declaring or ending a
  wait alone does not feed it. If scan execution stops, IRQ feeding stops.
- USB loss blanks and stops the RGB hardware before stopping its watchdog.
  It also cancels the wait. The separate settings-write watchdog cannot acquire
  this exemption because RGB scanning is stopped during that transaction.

This deliberately changes the foreground-stall allowance only inside a known,
bounded transport operation. It does not extend the hardware watchdog interval
or suppress invalid-state, scan-overrun, CPU-lockup or watchdog-reset safeguards.
Real faults remain latched; VIA edits, Restore defaults and USB resume do not
clear them. Brightness limits and manual-only flash saving remain unchanged.

## Stable activation

RGB initialization now requires 500 ms of observed USB configuration stability,
in addition to the existing initial 1500 ms startup guard. Reset, suspend and
detach events restart the observation window, including events occurring
between foreground observations. Normal startup therefore waits at least about
two seconds before lighting, and resume waits at least 500 ms after configuration
is observed. Keyboard typing is not delayed by this RGB window.

The suspend hook shuts down RGB before attempting to send a mouse release.
The test10.4 immediate IRQ shutdown on inactive USB is retained.

A real USB reset, suspend or loss of power can still blank the lights. This
release reduces flashes from brief configured intervals; it does not promise
uninterrupted lighting through every BIOS/OS handoff. A host that never configures
USB cannot satisfy the activation condition.

## Original Ducky comparison

The exact private Ducky 1.16 APROM was inspected and its USB control flow emulated.
Its suspend IRQ sets a RAM flag and its foreground dispatch selects separate
suspend/resume routines. See [USB_SHUTDOWN.md](USB_SHUTDOWN.md) for addresses and
the earlier investigation. In the tested non-suspended state, a USB bus reset
and HID BOOT/REPORT protocol selection do not select those shutdown/resume
routines. The hardware bodies of those routines are intercepted
in the automated test; original-firmware electrical behavior is not certified.
The QMK timing and watchdog policy must be assessed independently.

## Diagnostics version 2

The updated host tool retains legacy/version 1 support and adds read-only fields:

| Field | Meaning |
| --- | --- |
| `usb_wait_count` | Accepted finite-send wait declarations since this boot |
| `usb_wait_peak_scans` | Highest permitted scan count reached in one wait |
| `usb_event_count` | Observed reset/suspend/detach events since this boot |
| `usb_last_event` | 0 none, 1 reset, 2 suspend, 3 detach |
| `rgb_fault_reason_code=9` | Declared USB wait exceeded its scan budget |

These counters reside in RAM and reset at MCU restart. A nonzero wait count
does not by itself indicate a fault: sends that finish immediately also declare
a wait. A watchdog restart can again report reason 1 instead of the pre-reset
reason. No diagnostic flash writes were added.

## Physical acceptance test

1. Rebuild and flash from this source package as described in
   [INSTALLATION.md](INSTALLATION.md). If the old build is latched dark, disconnect
   USB power once before starting; never interrupt flashing. Existing saved
   settings remain compatible, and neither Restore defaults nor Save is required.
2. Boot directly into Windows and confirm typing, RGB, indicators and VIA controls.
3. Restart into BIOS, remain there for several minutes, type/navigate, then boot
   Windows without unplugging. After configuration settles, verify lighting and
   controls again. Record any dark interval and whether it persists.
4. Shut down and start the PC again with the keyboard connected. Repeat with the
   actual powered-USB/Fast Startup settings normally used on this PC.
5. Close VIA and run this package's `tools/diagnostics.py` with the workspace
   runtime Python (commands in [USB_SHUTDOWN.md](USB_SHUTDOWN.md)) after
   each failing case, before unplugging. Include the exact BIOS/Windows sequence.
   If a watchdog reset recurs, retain the whole JSON; do not treat it as permission
   to disable the reset guard.

Software emulation cannot establish real watchdog oscillator timing, electrical
power behavior, native installer behavior or compatibility with a particular BIOS.
