# Test10.5: manual settings writes only

Only the explicit Save action writes to `0x1e000–0x1ffff`. Startup, VIA edits,
JSON imports and Restore defaults only read flash or update RAM. No background
scheduler exists and old stored auto-save flags cannot enable one. Restore defaults
must be followed by Save if it should persist. See PERSISTENCE.md for details.
The firmware remains experimental; write timing and electrical behavior need hardware validation.

# Scope, flashing policy and hardware validation

This is an experimental community port, not Ducky firmware certification. The
distribution packages test10.5, extending the test9 firmware implementation. Earlier user tests
confirmed keyboard input, RGB and indicators; the test9 safety changes and this
new cross-platform assistant still require testing on the physical keyboard.

## Supported candidate

Only the observed **One 3 TKL RGB / DKON2187ST** configuration is allowed:

| Check | Required value |
| --- | --- |
| MCU PDID | `0x01205212` |
| Bootloader version | `51` |
| CONFIG0 | `0xf7ffff7c` |
| CONFIG1 | `0x00033200` |
| Bootloader USB | `0416:3f00` or `3233:8310`, usage page `1`, usage `0` |
| APROM image | Valid Cortex-M0 vectors, at most 120 KiB (122880 bytes), validated SHA-256 |

The MCU identity is **not proof of the keyboard model**. Other products can share
it. Confirm the PCB/product label in the final dialog. Multiple matching
bootloaders are rejected. Different bootloader/configuration values are refused,
not automatically added to the allowlist. Never use this on the Mini, SF,
full-size or non-backlit model.

## Install and restore

The assistant displays the D+L reconnection instructions on startup. When started
with the application still connected, it examines USB descriptors before you
unplug. The port's manufacturer and VIA interface identify it as QMK-compatible;
the original update interface identifies a Ducky-original-compatible device.
These are descriptor observations, **not cryptographic firmware identification**.
Once already in LDROM, the previous application is unknown: this protocol has no
implemented APROM read-back operation. Both choices remain available.

After you choose an action, it waits for one bootloader and opens it. A cancellable
**10-second wait** follows before any HID command. The assistant checks that only
the selected device remains present and aborts on an observed disconnect or change.
It then probes PDID, version and CONFIG, validates the image, and asks you to confirm
the target and write. Every recovery attempt repeats the full wait. A
default-No confirmation shows the action, identity, byte count and SHA-256. No
APROM write occurs before this confirmation. Setup itself never flashes anything.

Restoration always writes the exact official **Ducky RGB TKL 1.16** APROM, never a
previous QMK version. It does not promise to reset or preserve all Ducky settings
in data flash; that storage is not explicitly erased by the tool.

The command allowlist uses bootloader identification/synchronization, UPDATE_APROM
and RUN_APROM. There is no chip-erase, LDROM-write or CONFIG-write operation. Each
HID reply must have the expected sequence and length. A failed packet is not
silently repeated.

## Interrupted transfers

Before the first programming command, a flushed, atomically replaced marker is
saved outside the workspace:

- Windows: `%LOCALAPPDATA%\DuckyOne3TKLFlasher\pending.json`
- Linux: `~/.local/share/DuckyOne3TKLFlasher/pending.json`

The existing listener's marker and lock names are retained. A malformed marker
also forces restoration. Do not run an older flasher alongside this assistant.

If a transfer fails, the assistant automatically selects original recovery,
reopens the bootloader and validates it again. **Each recovery attempt asks for
confirmation**, including after reconnection, because this USB bootloader does not
provide a reliable unique board identity. There are at most three total attempts
per operation. Cancelling or closing with a pending marker keeps recovery required
next time. The assistant never sends RUN_APROM following an incomplete transfer.

Acknowledged packets are not flash read-back verification. The marker is cleared
after all packets are acknowledged and the start command is successfully sent;
this does not prove that the application booted. Confirm normal enumeration and
typing afterward. If needed, enter D+L again and choose restoration.

## RGB and voltage safeguards retained from test9

- RGB rows start blank. All seven rows are blanked before shifting new data.
- USB suspension/unconfigured state stops RGB scanning, all seven row gates, PC7 output enable, gray-clock output and the RGB watchdog directly from the scan IRQ.
- USB state is rechecked after serial transfer; a disconnect cannot re-enable the just-shifted bank.
- Engine/editor cleanup and initialization remain in foreground code. Genuine scan overruns still latch dark.
- USB loss cannot disable the separate watchdog used during explicit settings writes: that path has RGB scanning stopped.
- The final serializer caps every channel, including indicators and custom zones,
  at a user-selectable **0–90%** digital ceiling. VIA cannot raise it above 90%.
- Default master level 9 is `36864/65535`, approximately **56.25%**. Indicator
  brightness also defaults to level 9, has its own setting and still passes through the final ceiling.
- The watchdog uses independent LIRC with a nominal 1024-tick interval
  (about 102.4 ms at nominal 10 kHz). Actual oscillator/reset timing is not measured.
- Outside declared finite USB sends, the foreground heartbeat still faults at scan 51.
  A declared send has a separate 125-scan budget; retries cannot renew it. During
  that budget, only a successful scan may feed the unchanged hardware watchdog.
  Scan 126 faults, and scan overrun/invalid-state checks remain active throughout.
  See [BIOS_USB.md](BIOS_USB.md) for the precise timing and limitations.
- HardFault, unhandled exceptions and watchdog IRQ use a stackless row cutoff.
- The watchdog-reset path starts dark. A host hang does not get interpreted as a
  reason to raise voltage, LED current gain or brightness.
- No firmware CONFIG, LDROM, brown-out threshold or power-on-reset threshold
  writes are introduced. Factory trim is handled by the port's existing code.
- VIA edits and restoring defaults change RAM only. Only explicit Save writes the reserved settings partition.

The 11 Ducky brightness codes are preserved:

| Level | Digital code | Fraction of 65535 |
| --- | ---: | ---: |
| 0 | 0 | 0% |
| 1 | 1024 | 1.563% |
| 2 | 2048 | 3.125% |
| 3 | 4096 | 6.250% |
| 4 | 6656 | 10.156% |
| 5 | 9216 | 14.063% |
| 6 | 12288 | 18.750% |
| 7 | 16384 | 25.000% |
| 8 | 28672 | 43.751% |
| 9 | 36864 | 56.251% |
| 10 | 65535 | 100% before the final ceiling |

At the default 90% ceiling, the emitted code cannot exceed **58981**. This is a
digital PWM limit, not a claim of 90% optical brightness or electrical current.
It does not substitute for knowing the LED-driver current-setting hardware.

## Work requiring the keyboard or external instruments

1. Identify the actual LED-driver markings, current-setting resistors, rail
   regulators and MCU package on this board revision. A generic model name does
   not establish these component values.
2. Measure USB/LED supply voltage and total current under full-white output at
   each brightness level; compare with original firmware on the same unit.
3. Measure row duty cycle, blanking, shift/latch timing and the actual watchdog
   shutdown/reset interval with an oscilloscope or logic analyzer.
4. Measure LED-driver, regulator and PCB temperatures after sustained worst-case
   output. Test USB suspend/resume, disconnects and low-voltage behavior on a
   current-limited bench setup.
5. Validate emergency shutdown under injected faults and confirm D+L recovery
   remains reachable. Do not intentionally interrupt a live flash merely to test
   this assistant; use the supplied fault-injection tests first.
6. Test the Windows and Linux installers and GUI on real supported hosts,
   including HID access, mouse-only confirmations and USB reconnection behavior.

If LDROM no longer enumerates, this USB tool cannot restore the board. Recovery
then needs suitable Nuvoton SWD tooling, board access and a validated procedure.
