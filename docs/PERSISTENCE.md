# Test10.3: manual persistence only

The configuration is edited in RAM. **There is no automatic-save scheduler.**
Changing keys, layers, macros, RGB or zones does not write flash. Loading a VIA
layout JSON does not write flash in this port either. This differs from normal
QMK EEPROM backends, which can persist edits immediately.

Existing saved snapshots still take precedence at startup. After upgrading, use
**Restore defaults**, then **Save** if you want these new defaults to persist.
The initial CM painting color is white as well.

## Exactly two action buttons

| Action | Current RAM configuration | Keyboard flash |
| --- | --- | --- |
| Save current settings to flash | Unchanged | Saves a verified snapshot only if different |
| Restore defaults (RAM only) | Applies compiled defaults | Unchanged |

Restore defaults resets layers, keys, macros, QMK configuration, RGB and CM zones.
RGB returns to **Full Backlit (fixed white), R=10/G=10/B=10**.
Master brightness returns to level 9 (~56.25%), the ceiling to 90%, indicators to
level 9 (~56.25%), CM overlays off and mouse mode off. **Click Save afterwards only if you
want these defaults to remain after unplugging.** Otherwise the last saved snapshot
returns at the next power-up. If no valid saved snapshot exists, defaults load.
Restoring settings is separate from restoring original Ducky firmware.

The Arm button is removed: restoring defaults is now a reversible RAM-only action.
The standalone tool confirms before applying either action. VIA's direct reset
button operates in RAM without a separate Arm step.

## In VIA

1. Install test10.3 and import `via/ducky-one3-tkl-rgb.json` as a v3 definition.
2. Configure normally, then open **Settings storage → Keyboard flash**.
3. Use **Save current settings to flash** when satisfied.
4. Release all keys and finish CM editing. Keep USB connected until the last result
   says **Saved and verified** or **Already saved**. Reopen the menu to refresh labels.

The second action is **Restore defaults (RAM only; Save to keep)**. Reopen/reconnect
VIA afterwards to refresh the values it caches; the firmware cannot force old VIA
versions to refresh every page. **Pending changes** indicates RAM modifications,
not a scheduled write. No amount of idle time triggers a save.

The generic VIA `id_custom_save` packet is only acknowledged and does not persist
anything. Legacy Arm and auto-save commands are harmless no-ops, so an older JSON
cannot re-enable automatic saving. Test10/test10.1 snapshots load without startup
rewrites, even if their old auto-save flag was enabled.

## JSON files: definition versus profile

| File | Purpose | Includes our RGB/CM settings? |
| --- | --- | --- |
| `via/ducky-one3-tkl-rgb.json`, loaded under Design | Describes keys and custom UI controls; not a settings backup | No |
| `*.layout.json`, exported/imported under Save + Load | Layers/key assignments, macros and supported encoder assignments | No |

Verified against the current VIA `ViaSaveFile` type and save/load implementation
on 2026-10-16: `name`, `vendorProductId`, `layers`, optional `macros` and `encoders`.
There is no exported RGB field or custom-menu/CM zone snapshot in that format.
Source: [VIA save-load.tsx](https://github.com/the-via/app/blob/main/src/components/panes/configure-panes/save-load.tsx).

Exporting a VIA layout stores a file on the PC, not keyboard flash. Importing it
sends assignments to the keyboard; **our RAM-backed EEPROM keeps those changes
volatile until Save is pressed**. JSON itself does not provide this guarantee on
other QMK firmware. Profiles can be useful for trying different maps without wear,
but they must be reloaded after disconnecting unless saved to the keyboard.

The two-button tool does not add a proprietary JSON profile format or pretend
VIA layout files back up the Ducky lighting/CM configuration. Manual keyboard Save
includes those settings too; a complete PC-side RGB/CM export is not implemented.

## What the keyboard snapshot saves

- All four VIA layers, keys, macros and QMK EEPROM configuration.
- Ducky mode, enable state, channel levels and per-effect speeds.
- Master brightness, indicator intensity and the common 0–90% ceiling.
- CM1/CM2 assigned keys/colors and enabled overlays; mouse-mode preference.

Animation phase/RNG, pressed keys, host Caps/Scroll state, temporary palette and
uncommitted CM drafts are not saved. Saving pauses RGB temporarily. Unknown flash
contents or failed writes are reported and never retried in the background.

## Windows / Linux settings tool

Run `Settings-Ducky.cmd` / `Settings-Ducky.sh`, with the keyboard in normal mode
(not D+L) and VIA closed. The window has exactly two action buttons; status is read
when it opens. The updated tool requires protocol revision 3 (test10.2/test10.3) and refuses
older firmware before issuing writes: older Restore semantics included a flash save.

```text
python tools/settings.py --status
python tools/settings.py --save
python tools/settings.py --reset
```

`--reset` changes RAM only and returns status 9, **Defaults restored in RAM**.
The settings protocol revision is distinct from the compatible snapshot schema.

## Partition and transaction design

| Area | Address range | Rule |
| --- | --- | --- |
| QMK code/data image | `0x00000000–0x0001dfff` | Linker and flasher cap the image at 120 KiB |
| Snapshot bank A | `0x0001e000–0x0001efff` | Two 2048-byte erase pages |
| Snapshot bank B | `0x0001f000–0x0001ffff` | Two 2048-byte erase pages |
| Existing Ducky Data Flash boundary | observed `0x00033200` | Not modified or used by this feature |
| LDROM / CONFIG / SPROM | separate regions | No program/erase operations allowed |

Each bank contains a 32-byte header, 2048-byte QMK EEPROM image and 416-byte RGB
record. The header includes schema `0x000a0001`, sequence and complemented sequence,
CRC-32 and a final commit marker. Previously reserved RGB byte 24 is written as `0xa0` (off). Legacy `0` and
`0xa1` are accepted on load, but cannot enable automatic saving in test10.2 or test10.3.
The partition, payload size and schema remain compatible with test10/test10.1. The inactive bank is erased and written first;
every programmed word and erased page is read back. The CRC covers the header's
identity/length/sequence and the payload. The commit marker is written last. The
previous valid bank is retained until a later successful transaction needs it.

Before any write, the backend requires PDID `0x01205212` and the existing FMC Data
Flash boundary `0x00033200`. A blank partition can be initialized. A valid snapshot
establishes ownership of the reserved partition. With no valid snapshot and any
unknown/nonblank contents, saving is refused; the tool never offers a blind erase.
An interrupted first-ever save can leave this state. The keyboard still boots with
defaults, but that partition needs inspection before persistence can be enabled again.
This restriction prioritizes preserving unknown contents over automatic recovery.

The FMC operation runs from SRAM with interrupts masked only while the controller
is busy. RGB is suspended before the transaction; its banks and autonomous gray
clock are off. A separate watchdog window covers the transaction, fed only after
verified progress. Timeout while flash remains busy stays in SRAM for watchdog
recovery. All flash update permissions are closed and protected registers relocked
after each completed operation. Existing boot selection and clock settings are
preserved. CONFIG, voltage thresholds and LED driver gain are not changed.

Only explicit Save requests write flash. This avoids writes during ordinary
configuration changes, but the two-bank store is not a full wear-leveling system. Power-loss behavior is tested in software; analog brown-out effects,
maximum erase/program latency and watchdog reset behavior require the physical board.

## Compatibility and validation still required

The EEPROM layout is pinned to this QMK commit and snapshot schema. Within the same
schema, the VIA build-date marker is refreshed in RAM after loading so rebuilding
on a different date does not alone discard the saved keymap. A future incompatible
layout must bump the snapshot schema and supply a deliberate migration policy.

Persistence is intended across power cycles. Preservation through the original
Ducky updater, older flashers or future firmware images is **not guaranteed**: their
erase ranges have not been verified here. Export a VIA layout backup before changing
firmware. Original Ducky data is outside our write range; restoring Ducky does not
interpret or import QMK snapshots.

First physical test:

1. Flash test10.3 and import the matching VIA definition.
2. Change a key/RGB setting, use Save, check success and reconnect: settings should persist.
3. Make different changes without Save and reconnect: the previously saved settings should return.
4. Restore defaults without Save and reconnect: the previously saved settings should return.
5. Restore defaults, click Save, verify success and reconnect: defaults should persist.
6. Load a VIA layout JSON, inspect the assignments, then use Save only if wanted.
7. Check normal USB suspend/resume after saving. Do not intentionally interrupt a
   physical write to test fault recovery; use the included simulated-cut tests.

If storage reports a target mismatch, unknown contents or a write failure, retain
the message and stop retrying blindly. No claim of physical persistence validation
is made before these checks have been performed on the target keyboard.

## Primary references

- [QMK persistent configuration](https://docs.qmk.fm/feature_eeprom): limited write endurance; avoid writing for every UI event.

- [Nuvoton NUC1261 FMC driver](https://github.com/OpenNuvoton/NUC1261BSP/blob/master/Library/StdDriver/inc/fmc.h): 2048-byte pages, program/erase commands and timeout handling.
- [Nuvoton NUC1261 register definitions](https://github.com/OpenNuvoton/NUC1261BSP/blob/master/Library/Device/Nuvoton/NUC1261/Include/NUC1261.h): FMC update enables, Data Flash boundary, failure/brown-out behavior.
- [VIA custom controls](https://github.com/the-via/app/blob/main/src/components/panes/configure-panes/custom/custom-control.tsx): button value and status-label encoding.
- Original APROM 1.16: observed data-boundary constant at offsets `0x49bc` and `0x9444`; the loader/configuration setup starts at `0x46c8`. This is bounded reverse-engineering evidence, not a proof of every stock flash-access path.
