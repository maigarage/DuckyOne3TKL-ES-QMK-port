# test10.5 validation — 2026-10-17

This release changes finite USB-send handling, RGB configuration stability and
read-only diagnostics. Rebuild and flash to install it. No physical keyboard
was connected during these checks.

- Pinned QMK/ChibiOS build with Arm GCC 13.2.1 passed.
- Final image: **56716 bytes**; static RAM including declared stacks:
  **16668 bytes** out of 20480. This is not a measured worst-case stack bound.
- Final SHA-256: `8ef60baf2a1e5d73c8f7625e0a0a8a4ad082d6de4a4beba58ff16a8d23ce55b6`.
- **44 host tests passed**, including diagnostics v2/legacy support and a native
  harness executing the shipped USB send function with mocked queue operations.
  The transport harness covers retries, single lease ownership, infinite waits,
  inactive USB, immediate timeout and normal completion.
- Final linked disassembly contains the finite-send begin/end calls and all three
  USB lifecycle event calls. The USB transport hook is not only a standalone stub.
- Standalone and final-linked ARM checks cover 100-scan waits, the 125-scan limit,
  refusal to renew the allowance, scan-overrun cutoff, USB-loss cancellation,
  flash-watchdog ownership, no feed without scanning, 500 ms stability with an
  intervening reset, and ordinary foreground timeout at scan 51.
- Full RGB and USB shutdown regressions cover all 12 modes, brightness/indicator
  limits, CM overlays, settings roundtrip, IRQ-only pauses, transfer-time USB loss,
  repeated resume, duplicate wake and timer wrap.
- Final linked safety, settings-protocol and SRAM flash-backend checks passed.
  Original/relocated engine comparison covers 480 updates. LUT and mouse checks
  passed. Storage tests cover 625 injected cut points and 16 persistence cases.
- Original Ducky 1.16 USB control-flow emulation covers suspend/resume, bus reset
  and HID BOOT/REPORT protocol selection. Hardware transition bodies are
  intercepted; this establishes branch selection, not real LED-driver behavior.

The final build keeps the foreground task and USB event/wait entry points visible
for linked regression tests. Timer, USB and watchdog registers are modeled.
No real watchdog expiry, power transition, BIOS handoff, Windows installation,
current, voltage, temperature or worst-case interrupt latency was measured.
The latest user report (`RSTSTS=0x64`, reason 1, zero scan sequence) establishes a
watchdog-startup inhibit, not the precise original stall. Follow the physical
acceptance steps in [BIOS_USB.md](BIOS_USB.md).

---

# test10.4 validation — 2026-10-17

This release changes the RGB USB lifecycle and read-only diagnostics. It requires
rebuilding and flashing. No physical keyboard was connected in this validation.

- QMK build with Arm GCC 13.2.1 and all pinned upstream revisions passed.
- Final image: **56308 bytes**; static RAM including declared stacks:
  **16636 bytes** out of 20480. This is not a measured worst-case stack bound.
- Final SHA-256: `3e755ed417ac1ab9484331d4b269a3804064763c352f056ac292644f0cefe570`.
- **42 host tests passed**, including extended/legacy diagnostics and malformed
  response rejection; all diagnostic requests are read-only VIA GET operations.
- The new ARM USB regression passed against both the standalone controller and
  the final linked firmware: IRQ-only pause with delayed foreground, USB loss
  during serial transfer, 20 reconnect cycles in each target, duplicate wake,
  32-bit timer wrap, flash-watchdog ownership and latched real faults.
- Full RGB regression passed for the corrected controller, including all 12
  modes, brightness/indicator limits, CM overlays and settings roundtrip.
- Final linked image passed emergency cutoff, output ceiling, USB gating,
  watchdog, settings-protocol and SRAM flash-backend checks.
- Storage tests passed **625 fault-injection cut points** and **16 native
  persistence-controller cases**. No automatic settings saving was introduced.
- Original-versus-relocated engine comparison passed all 480 updates. Brightness
  LUT and mouse regression checks passed.
- Actual original 1.16 USB IRQ and foreground branch selection passed the new
  stock-USB control-flow test. Hardware transition routines were intercepted;
  this does not prove physical original-firmware timing.

The final build retains the RGB task as a non-inlined symbol for linked tests.
The full standalone RGB run preceded that symbol-retention annotation; the
final linked safety/USB/settings/flash checks used the final image listed above.
Timer, USB and watchdog registers are modeled. No real watchdog expiry, analog
power transition, PC shutdown, Windows installer or electrical behavior was
measured. The user must run the acceptance steps in [USB_SHUTDOWN.md](USB_SHUTDOWN.md).
The reset evidence includes watchdog and low-voltage flags; chronology and the
physical cause of the reported event remain unproven.

---

# GitHub source package validation — 2026-10-16

This package integrates the 10-second bootloader wait and English documentation.
Its firmware source overlay and VIA definition are byte-for-byte identical to
those in test10.3. Only the host assistant, host regression tests and documentation
changed; no new firmware binary was built for this packaging update.

- **39 Python host tests passed**, including five bootloader-wait tests with a
  virtual clock and fake USB enumeration: full 10-second delay with no HID writes,
  cancellation, disappearance, path replacement and multiple matching devices.
- **625 storage fault-injection cut points passed**, including torn writes/erases,
  corruption fallback, unknown-region refusal and unchanged-save write avoidance.
- **16 native persistence-controller cases passed** using the current source.
- Bash syntax, Python tool syntax, VIA JSON and local Markdown file links passed.
- Archive entries and source SHA-256 hashes were checked; no firmware binaries,
  vendor executables, generated RGB blobs or Python caches are included.

These are container-based software checks, not a new native Windows/Ubuntu setup
trial or a physical bootloader test. Existing Windows launch regression coverage
remains in CI; it was not executed on Windows in this packaging run. Firmware
build and linked ARM evidence below belongs to the earlier test10.3 build.

All sections below are historical reports for their named revision. References to
Arm or automatic saving in test10/test10.1 do not describe current behavior.

---

# Test10.3 validation — 2026-10-16

Current change: Full Backlit fixed white (R/G/B levels 10/10/10), master level 9,
and all three independent indicators at level 9 when their functions are active.
The 90% ceiling and manual-only persistence are unchanged from test10.2.

- Clean QMK build and finalizer passed: **56552 bytes**, SHA-256
  `edd89c38660eadab63a9d32079863b4f0f1c27479e6b499282ab265818a64ded`.
- Static RAM including declared stacks: **16632 bytes**.
- Actual ARM RGB code was checked at cold initialization and after resetting changed
  settings: mode 0, master 9, channels 10/10/10, indicators 9, ceiling 90, CM off.
- GPIO serializer output passed for every keyboard RGB slot and all three enabled
  indicators at level 9. The inherited stock red low-bit encoding was preserved.
- Final linked binary passed the existing ceiling/emergency/watchdog/USB safety suite.
- VIA JSON validated and every packaged overlay source matches the build checkout.
- Existing RGB and persistence tests have their default-value expectations updated.
  The full RGB regression and persistence fault-injection suite were not rerun for
  this default-value-only change; earlier revision results below are baseline evidence.

Existing valid saved snapshots retain priority at startup. Apply Restore defaults
and then Save to persist the new settings after upgrading. No physical keyboard
was accessed; actual brightness and power-cycle behavior remain physical checks.

---

# Test10.2 validation — 2026-10-16

Current revision: manual Save only, defaults reset in RAM, two action buttons.
Older sections below document the corresponding old binaries, not this revision.

- Clean build and finalizer passed. Image: **56552 bytes**, SHA-256
  `1a9b0426e6ab6e9e8bd82d418d46631faec551b41a19585f6584e84256bac727`.
- Static RAM including declared stacks: **16632 bytes** out of 20480.
- **34 host Python tests** passed, including rejection of older protocol revisions
  before issuing a Save/Restore command and the new RAM-only reset result.
- **16 native controller/store integration cases** passed: idle for 24 simulated
  hours; repeated EEPROM/RGB edits; VIA custom-save; old auto-save and Arm commands;
  manual-only writes; duplicate-save deduplication; RAM-only defaults; defaults saved
  only after Save; previous snapshot retained after unsaved reset; key/USB/CM guards;
  failed write with no retry; unknown/incorrect target; old snapshots with auto on.
- Actual linked ARM command handler passed protocol revision 3, legacy no-ops,
  explicit Save, RAM-reset request and busy/unknown command checks.
- Final linked binary passed the safety suite (ceiling, emergency cutoff, watchdog,
  early shutdown and USB/scan gating) and SRAM flash backend bounds/permissions.
- Dual-bank store passed **625 fault-injection cut points**, including partial
  operations, corrupted records, fallback and no-write identical snapshots.
- The RGB implementation and safety/FMC drivers are unchanged from test10.1.
  Its full RGB/mouse and 480-step stock-engine comparison remains baseline evidence;
  the complete standalone RGB simulation was not repeated for this settings-only change.
- VIA JSON and Python source validation passed. Installer dependency/bootstrap code
  is unchanged. No end-to-end Windows installation or physical keyboard test was run.

These are software checks. Actual power-cycle persistence, USB behavior and physical
flash/electrical timing still need the keyboard. See PERSISTENCE.md for test steps.

---

# Test10.1 validation — 2026-10-16

This historical section covers test10.1, including its former auto-save and Arm
behavior. Those features are disabled/removed in the current test10.3 release.

- Clean QMK/VIA build with pinned dependencies and GCC 13.2.1 passed.
- Final code image: **57036 bytes**, SHA-256
  `b37f0bd42177be809beb1b16077f1a5ff04d61ff3258fe0d169f12f6e51dc7f9`.
- Static RAM including declared stacks: **16656 bytes** out of 20480.
  This is not a measured maximum stack/heap requirement.
- ELF/BIN agreement, vectors, SRAM flash routine, USB descriptor and reserved
  partition boundary checked by the finalizer.
- **34 Python host tests** passed (flashing policy, setup source reuse, settings
  protocol and the separate GUI arm-before-reset requirement).
- **18 native controller integration cases** passed using the actual persistence
  controller and dual-bank store with simulated MMIO/flash: captured reset rejection,
  arm expiration/consumption, timer wrap, edit batching, write spacing, RGB changes,
  unchanged saves, USB/key/CM gating, failure pause/manual retry, unknown partition,
  target mismatch, queued commands, policy persistence, legacy test10 snapshot compatibility and restored defaults.
- Actual linked ARM command handler passed the captured `7 2 3 1` regression:
  valid ACK with locked status and no queued reset; arm alone does not queue reset;
  reset accepted before 10s, rejected at 10s, consumed once; wrap-safe timers;
  busy duplicates ACKed; auto-save toggle supported; unknown IDs still rejected.
- Full RGB regression passed: all 12 modes, original 11-level intensity LUT,
  brightness cap across effects/indicators/queued frames, palette, CM recording,
  snapshot roundtrip, USB/fault behavior and mouse state-machine regression.
- Final linked binary passed stackless emergency cutoff, watchdog and RGB scan
  safety checks; linked SRAM flash backend passed range/identity/permission checks.
- Original-vs-relocated stock engine matched for **480 updates**.
- Dual-bank transaction fault injection passed **625 cut points**, including
  partial writes/erases, corrupt snapshots, unknown partition and fallback cases.
- Python compilation and Linux setup Bash syntax passed. Windows end-to-end setup
  and the interactive Tk window on a real Windows host have not been run here.

No physical keyboard was accessed or flashed. Timing, flash endurance, power-loss
behavior on the actual board and actual USB interaction remain hardware checks.
See PERSISTENCE.md for the behavior and first physical verification steps.

---

# Test10 validation — 2026-10-16

This section describes test10. Older dated sections below are historical baseline
evidence, not claims that test10 is byte-identical to test9.

- QMK/VIA build passed with the same pinned QMK/HAL dependencies and GCC 13.2.1.
- Final image: **56084 bytes**, SHA-256
  `ed5682a4ab1d35eb208c9d94c509976a4047cc332e9ad3c865405abccd6af9e0`.
- Static RAM including declared stacks: **16632 bytes** out of 20480; the remaining
  margin is not a measured worst-case dynamic heap/stack guarantee.
- Finalizer checked ELF/BIN agreement, vectors, RAM, test10 USB identity, code image
  below `0x1e000` and SRAM placement of `flash_operation`.
- **33 Python host tests passed**, including six settings-tool protocol tests.
- The actual transaction C code passed **625 injected cut points**: normal cuts,
  partial word/page operations, corrupted snapshots, fallback, first-save failure,
  unknown-region refusal, no-write identical saves and the default-reset transaction.
- The actual linked SRAM FMC routine passed boundary/program/erase, failure/relock,
  address rejection and wrong-target tests in a register model. Instruction fetches
  stayed in SRAM while the modeled FMC was busy. No CONFIG/LDROM/SPROM enable was used.
- The final linked firmware passed the retained safety tests: output ceiling,
  stackless emergency cutoff, watchdog setup, USB gating, overrun and early cutoff.
- The full ARM RGB harness passed all 12 modes, brightness levels, indicators, zones,
  palette, ceiling and fault/suspend behavior. Original brightness LUT comparison
  passed all 11 levels; stock-versus-relocated engine comparison passed 480 updates.
  The mouse state-machine test also passed.
- RGB snapshot export/import roundtrip passed, including CM overlays, mouse preference,
  original per-mode speed parameters, defaults and malformed-field rejection.
- Python compilation, Bash syntax and the PowerShell-to-Bash launch regression passed.

These checks did not write a physical keyboard. Actual flash timing, undervoltage,
watchdog recovery during a real flash stall, power-cycle persistence, real USB
behavior and Windows end-to-end installation remain hardware/host checks.
See [PERSISTENCE.md](PERSISTENCE.md) for the first physical test and known limits.

---

# Validation of the cleaned source distribution

## Installer/source-download fix — 2026-10-16

The Windows screenshot showed `unexpected EOF while looking for matching ')'`
before source download/compilation. The `bash -lc` expression was replaced with a
direct `bash --login SCRIPT_FILE` invocation, removing nested native/shell quoting.
The regression test executes a script with spaces and parentheses in its path;
it passed with PowerShell 7.4.6 and Bash on Linux. An equivalent Windows PowerShell
5.1/Git Bash check is included in CI, but has not been executed on a Windows host
in this environment.

A new, empty source checkout was fetched from the pinned upstream repositories
using shallow, blob-filtered sparse checkout. The final directory selection built
successfully with GCC 13.2.1. Only our Ducky keyboard is present. Measured file
contents were approximately 14.0 MiB of source and 9.1 MiB of Git metadata/objects,
excluding compiler tools, build outputs and Python caches. Physical filesystem
allocation and actual network transfer sizes can differ from those figures.

All 27 host tests pass: the previous 23 flashing tests plus four checks protecting
existing source revisions, origins and local edits. Reusing all five downloaded
checkouts was also exercised. Bash syntax and the actual PowerShell-to-Bash script
invocation passed. The flashing protocol was not changed.

Comparing an initial rebuilt image against test9 detected that the build checkout
had lost the overlay's USB protected-register unlock/lock hooks. The packaged
overlay already contained those hooks. Copying now assigns fresh timestamps and
the builder checks every overlay file's SHA-256 after compilation, before staging
firmware, to reject sources altered during a build. All overlay differences
against the baseline source are license/attribution comments or whitespace;
firmware logic and the flashing protocol remain unchanged.

The October 16 build passes linked-image structural verification: 53056 bytes,
15928 bytes of static RAM including stacks, SHA-256
`17e3014a478c60dac576976cc1b706f147bbf1feebcd5a44f44546572eacbd1f`.
This hash describes this build, not a universal hash across dates/toolchains.
The binary differs from the October 15 baseline only at offsets `0x25d6` and
`0x2ace`, both date-derived VIA initialization bytes (`0x15` to `0x16`).
Linked-firmware safety emulation and all 11 original brightness LUT levels were
rechecked successfully on the corrected build. The original-versus-relocated
engine comparison also passed all 480 updates across 12 modes. No device was flashed.

## Baseline validation — 2026-10-15

Validation date: 2026-10-15. Baseline: test9. No device was flashed during this
packaging task. No RGB behavior, voltage threshold or watchdog configuration was
changed as part of the cleanup.

| Check | Result |
| --- | --- |
| Official Ducky updater download | Exact SHA-256 match to the analyzed 1.16 executable |
| Original APROM extraction | 43746 bytes, exact expected SHA-256 |
| Regenerated native RGB assembly | Exact instructions/data/relocations match to baseline; generated comment differs |
| Regenerated initial RAM and engine RAM | Byte-for-byte match to baseline snapshots |
| Relocation count | 68 reviewed RAM literals |
| Full QMK build on Linux | Passed with Arm GCC 13.2.1 |
| Linked ELF/BIN, vectors, RAM, required handlers and USB identity | Passed |
| Fake-HID flashing-policy suite | 23 tests passed; no real HID imported/opened |
| ARM RGB harness | Passed for all 12 modes, original nonlinear levels, indicators, zones, palette and hard ceiling |
| Actual linked-firmware safety emulation | Passed: all banks bounded, stackless cutoff, watchdog setup, USB gating, overrun and early cutoff |
| Original versus port brightness LUT | All 11 codes match |
| Original versus relocated engine | 480 updates with byte-for-byte RGB RAM and RNG-state agreement |
| Mouse state-machine C test | Passed: mappings, chord, ownership/release and suspend |
| Python source compilation | Passed |
| Bash syntax | Passed |
| PowerShell parser | Passed with PowerShell 7.4.6 on Linux |

The rebuilt image is 53056 bytes, with SHA-256:

`c1a20a40386273a5d9262201f3d9972ab897cf4006ee294f019ee2fb99d7a132`

It differs from the prior test9 image in two build-date-derived VIA initialization
bytes (October 12 versus October 15). The extracted native RGB code and all port
logic remain unchanged. Future build dates/toolchains may produce other hashes;
the assistant reads the SHA-256 from the locally validated build manifest. That
manifest detects accidental changes; it is not a cryptographic publisher signature.

Host tests cover default-deny confirmation, every observed identity field,
corrupt images/vectors, incomplete writes, invalid replies/sequences, timeouts,
disconnects, durable pending markers, original-only restoration, recovery
confirmation, single-instance locking and multiple-bootloader rejection.

This validation did **not** perform a fresh end-to-end OS installation, run the
Windows executable installers, verify Windows HID behavior, test GUI interaction
on physical hosts, measure current/voltage/temperature or certify real-time
timing. The included CI workflow is prepared for Windows/Linux host tests; it has
not been run on GitHub as part of this task. Remaining checks are explicit in
[SAFETY.md](SAFETY.md).
