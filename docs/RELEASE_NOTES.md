# Release notes

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
