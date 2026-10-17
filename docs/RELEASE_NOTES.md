# Release notes

## test10.5 — 2026-10-17

- Corrects the mismatch between finite 100 ms USB send waits and the ordinary
  50-scan foreground heartbeat. One non-renewable 125-scan allowance covers the
  entire send/retry loop. Only healthy completed scans feed the unchanged hardware
  watchdog during this allowance; overrun, invalid state and timeout still fault.
- Requires 500 ms of observed stable USB configuration before starting RGB after
  the initial guard or a pause. USB reset/suspend/detach events restart the window.
- Stops RGB before sending a mouse release in the suspend hook.
- Adds read-only diagnostics version 2: wait count/peak, USB event count/type and
  wait-budget fault reason 9. Keeps old diagnostic fields and legacy host support.
- Preserves fail-dark watchdog/CPU-lockup startup guards, the 90% ceiling, manual
  settings Save, RAM-only defaults, storage schema and 10-second bootloader wait.
- Adds transport-source and ARM regression tests. Physical BIOS-to-Windows and
  power-transition behavior still require the user's keyboard.

See [BIOS_USB.md](BIOS_USB.md) for evidence, limitations and acceptance steps.

## test10.4 — 2026-10-17

- Fixes a software gap during USB shutdown: the RGB IRQ now stops its timer,
  every row, output enable, gray clock and watchdog when USB is inactive,
  even if foreground processing is delayed. Checks USB again after shifting.
- Resumes from foreground once USB is configured. Duplicate wake notifications
  do not reinitialize a running renderer.
- Preserves fail-dark behavior for real heartbeat, overrun, invalid-state,
  watchdog-start and watchdog/CPU-lockup reset faults. No automatic fault clearing.
- Preserves flash-watchdog ownership, manual Save, RAM-only Restore defaults,
  level-9 white defaults, the 90% ceiling and the 10-second bootloader wait.
- Fixes the startup-only delay incorrectly applying again at the 32-bit
  millisecond wrap (about 49.7 days); this was not the reported one-day failure.
- Adds explicit fault reasons and USB-pause/scan counters to read-only diagnostics.
  The new host diagnostic also works with old firmware, without the extra fields.
- Adds ARM USB lifecycle regression tests and a checked original Ducky 1.16
  suspend/resume control-flow comparison. See USB_SHUTDOWN.md and VALIDATION.md.

This firmware must be rebuilt and flashed. Actual PC shutdown behavior still
requires testing on the keyboard; software simulation is not a physical test.


## test10.3 GitHub source package — 2026-10-16

- Integrates the 10-second bootloader settle wait in `tools/manage.py`.
- Applies the wait before HID commands for installation, original restoration
  and every recovery attempt. Supports cancellation and aborts on an observed
  bootloader disconnect, replacement or multiple matching devices.
- Adds five virtual-clock / fake-USB regression tests for this gate.
- Rewrites the repository README with Windows and Ubuntu setup/run instructions,
  separate project/workspace paths, VIA setup and GitHub publishing guidance.
- Adds installation troubleshooting and clarifies manual CM-zone persistence.
- Updates current documentation to test10.3 and the 120 KiB image limit; preserves
  prior validation results as explicitly historical evidence.

The keyboard source overlay and VIA definition are unchanged from test10.3.
The original white defaults, manual Save policy, RAM-only Restore defaults,
90% ceiling and two-bank settings format are retained. The countdown is a host
assistant change and does not require reflashing an already installed test10.3.

This is a source distribution with pinned upstream downloads and locally generated
vendor inputs. No vendor updater, original image or combined firmware binary is
included. See [THIRD_PARTY.md](../THIRD_PARTY.md).
