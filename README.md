# Ducky One 3 TKL RGB — Experimental QMK / VIA Port

Community firmware for the **Ducky One 3 TKL RGB (DKON2187ST)** with VIA remapping,
four layers, macros, Ducky-derived lighting effects and explicit settings storage.

**Release: test10.5 — bounded USB waits and stable lighting startup.**
This is a complete project source package, not a ready-to-flash binary release.
Setup downloads pinned dependencies and the original vendor input, builds locally,
and checks the result. **Setup never flashes the keyboard.**

This project is experimental and is not endorsed by Ducky, QMK or Nuvoton.
Read [compatibility and safety](docs/SAFETY.md) before installing.

## Compatibility

| Item | Supported target |
| --- | --- |
| Keyboard | Ducky One 3 TKL RGB, model DKON2187ST; development unit uses the Spanish layout |
| MCU identity | NUC1261, PDID `0x01205212` |
| Bootloader / configuration | Version `51`, CONFIG0 `0xf7ffff7c`, CONFIG1 `0x00033200` |
| Windows setup | Windows 10/11 x64, Windows PowerShell 5.1 or PowerShell 7 |
| Ubuntu setup | Ubuntu 24.04 LTS, x86_64, local graphical desktop |
| Configuration | VIA with the included custom v3 definition |

Other One 3 sizes, non-RGB boards and different chip/configuration revisions are
not supported. Matching USB identifiers alone does not establish compatibility.
The assistant checks the chip/configuration; you must also check the keyboard label.
Windows and Ubuntu setup paths are provided; native end-to-end installation and
hardware behavior are not certified by the included automated tests.

## Features

- Four VIA layers and editable key assignments/macros.
- Twelve lighting selections: Full Backlit, Wave, Color Cycle, Rain Drop, Ripple,
  Rainbow Reactive, Reactive, Halo, Breathe, Radar, Laser and Off.
- Two custom per-key lighting overlays, CM1 and CM2.
- Separate Caps Lock, Scroll Lock and mouse-mode indicators.
- Coordinated RGB/watchdog pause when USB becomes inactive, with resume after 500 ms of observed configuration stability.
- Bounded handling of finite USB sends, with scan-progress and timeout safeguards.
- Read-only fault, USB-wait and lifecycle diagnostics.
- Firmware-enforced maximum lighting ceiling of 90%.
- Manual settings persistence: edits affect RAM; only **Save** writes settings flash.
- Original Ducky 1.16 restoration through the same assistant.
- Cancellable 10-second wait after bootloader detection/opening, before HID commands.

Defaults are white Full Backlit, RGB channel levels 10/10/10, master brightness
level 9 (approximately 56.25%) and indicator brightness level 9. Indicators light
only when their corresponding functions are active. Previously saved settings
still take precedence when the keyboard starts.

## Upgrading from test10.3 / test10.4

This update changes the keyboard firmware: rebuild and flash it. Replacing only
the VIA JSON or `manage.py` does not install the fix. Reuse your existing build
workspace when running Setup from this new source folder, then use Manage-Ducky
to install QMK. Disconnect the keyboard from USB power once before the upgrade
to clear the old fail-dark state; do not interrupt a flash operation. Saved
settings retain the same schema. See [BIOS and USB startup](docs/BIOS_USB.md)
for the timing policy, diagnostic fields and physical acceptance test. Genuine
USB resets or power loss may still blank the lights; no automatic fault clearing
is introduced.

## Before setup

Keep two separate folders:

| Folder | Example on Windows | Example on Ubuntu | Purpose |
| --- | --- | --- | --- |
| Project | `C:\DuckySource\ducky-one3-tkl-qmk` | `$HOME/ducky-one3-tkl-qmk` | This repository: source, scripts and documentation |
| Build workspace | `C:\DuckyOne3` | `$HOME/DuckyOne3` | Downloaded tools, dependencies, private inputs and build results |

Use a local, absolute workspace path without spaces. Choose an empty directory or
reuse an existing Ducky workspace. Do not select the project folder as the workspace.
Initial setup needs Internet access and downloads a compiler and dependencies.
Keep the project folder after setup: the generated launchers refer to its tools.

## Windows: setup and run

1. Download and extract the source ZIP, or clone this repository. Open the folder
   containing `Setup-Windows.cmd`.
2. Double-click **`Setup-Windows.cmd`**. Alternatively, run this from PowerShell:

   ```powershell
   .\Setup-Windows.cmd
   ```

3. Enter `C:\DuckyOne3` when asked for the working directory.
4. Let setup finish. It installs or reuses Python and QMK MSYS, runs host tests,
   downloads the original Ducky input, compiles QMK and validates the image.
   Dependency installers run unattended; Windows may request UAC approval.
5. Open **`C:\DuckyOne3\Manage-Ducky.cmd`** for installation or original restoration.

Windows uses the existing HID driver. Do not replace the keyboard driver with
Zadig for this workflow. Compiler output is saved to `C:\DuckyOne3\build.log`.
See [Windows troubleshooting](docs/INSTALLATION.md#windows-troubleshooting).

## Ubuntu: setup and run

On **Ubuntu 24.04 LTS x86_64**, extract the project to your home directory and run:

```bash
cd "$HOME/ducky-one3-tkl-qmk"
bash setup-linux.sh
```

If GitHub named the downloaded folder differently, use that actual folder name.
Accept the default workspace (`$HOME/DuckyOne3`) or enter another absolute path
without spaces. Run setup as your normal desktop user. It invokes `sudo` for
system packages and udev rules and may ask for your password.

Setup installs the compiler, Python/Tk and USB dependencies with `apt`, creates
separate Python environments, runs tests, builds QMK and validates the result.
After successful setup:

```bash
"$HOME/DuckyOne3/Manage-Ducky.sh"
```

Compiler output is saved to `$HOME/DuckyOne3/build.log`. The installed udev rules
provide HID access to the active local desktop user. Reconnect the keyboard if
permissions have not refreshed. See [Ubuntu troubleshooting](docs/INSTALLATION.md#ubuntu-troubleshooting).

## Install QMK or restore Ducky

1. Close VIA, Ducky's updater and other keyboard tools. Start **Manage-Ducky** while
   the keyboard is still in normal mode when possible.
2. Choose **Install QMK** or **Restore Ducky original**.
3. Unplug the Ducky, hold **D + L**, then reconnect it. Release the keys when the
   assistant reports bootloader detection.
4. Wait for the **10-second countdown**. No HID command is sent during this wait.
   Cancellation or a detected device-selection change stops the attempt.
5. The assistant identifies the bootloader and validates the image. Check the
   model and action in the confirmation dialog, then confirm to start writing.
6. Keep USB connected until all packets are acknowledged and application startup
   is requested. Verify typing, USB enumeration and lighting afterward.

The same wait applies to installation, restoration and every recovery attempt.
Its setting is `BOOTLOADER_SETTLE_SECONDS = 10` in `tools/manage.py`.
The wait is separate from the old settings-reset **Arm** button, which is removed.

If a transfer is interrupted, reopen the assistant. A persistent marker forces
restoration of the pinned original Ducky 1.16 firmware; each recovery attempt
still requires confirmation. Do not delete the marker to bypass recovery.
APROM transfer acknowledgements are not full firmware read-back verification.
See [recovery behavior](docs/SAFETY.md#interrupted-transfers).

## Connect VIA and save settings

1. Open [VIA](https://usevia.app/) in a browser with WebHID support, such as Chrome
   or Edge, with the QMK firmware running normally.
2. Enable the **Design** tab in VIA settings, then load
   **`via/ducky-one3-tkl-rgb.json`** as a **v3 definition** (V2 definitions disabled).
3. Authorize the keyboard when requested and open **Configure**.
4. Edit keys, layers, macros and lighting. These changes are active immediately in
   the keyboard's RAM, even after closing VIA.
5. To keep them after unplugging, open **Settings storage → Keyboard flash** and
   click **Save current settings to flash**. Release all keys and finish any CM
   recording; wait for **Saved and verified** or **Already saved**. Reopen the
   menu if its result label has not refreshed.

**Restore defaults (RAM only; Save to keep)** resets the live configuration.
Click **Save** separately if those defaults should survive a power cycle.
There is no automatic save. If you still see **Arm reset**, replace the older VIA
Design definition with the JSON from this package; flashing does not replace it.

VIA's **Save + Load** layout JSON backs up keymaps/macros, not this port's custom
RGB/CM settings. The Design JSON describes the interface and is not a backup.
See [persistence](docs/PERSISTENCE.md) and [lighting / shortcuts](docs/CONTROLS.md).

Optional standalone settings tool, with VIA closed and the keyboard in normal mode:

```powershell
C:\DuckyOne3\Settings-Ducky.cmd
```

```bash
"$HOME/DuckyOne3/Settings-Ducky.sh"
```

## Repository contents and development

| Location | Contents |
| --- | --- |
| `source-overlay/` | All project modifications to the pinned QMK/ChibiOS sources |
| `tools/` | Setup helpers, source generation, build validation, flashing and settings tools |
| `scripts/` | MSYS build entrypoint and Linux udev rules |
| `via/` | Current English VIA v3 definition |
| `tests/`, `.github/workflows/` | Host policy tests, emulation harnesses and CI |
| `research/` | Matrix, RGB geometry and indicator-bank analysis scripts |
| `docs/` | Installation, rebuilding, controls, persistence and validation documentation |
| `LICENSE`, `NOTICE`, `THIRD_PARTY.md`, `licenses/` | Licensing and attribution |

Run host tests without connecting a keyboard:

```bash
python3 -m unittest discover -s tests -v
```

On Windows, use the workspace runtime's `Scripts\python.exe` instead of `python3`.
See [BUILD.md](docs/BUILD.md) for pinned dependencies, rebuild commands and firmware
emulation tests. [VALIDATION.md](docs/VALIDATION.md) separates current checks from
historical results and outstanding hardware validation.

## Publishing on GitHub

Upload the **contents** of the `ducky-one3-tkl-qmk` folder so that this `README.md`
is at the repository root. Include the dotfiles, particularly `.github/` and
`.gitignore`. Do not upload the separate build workspace.

This distribution includes all project source changes and build tools. Unmodified
upstream QMK/ChibiOS sources are fetched at pinned commits during setup.
The exact RGB engine contains machine code extracted locally from Ducky's original
firmware; it is not recovered vendor C source. Setup checks the official input's
SHA-256 and never executes the vendor updater.

Original Ducky firmware, vendor executables, generated RGB blobs and combined
firmware binaries are excluded from the public archive. No vendor redistribution
permission is asserted. Keep those generated files out of public repositories and
releases. See [THIRD_PARTY.md](THIRD_PARTY.md) for the source and licensing boundary.

To reproduce a clean source ZIP:

```bash
python3 tools/package.py /path/outside/the/repository/Ducky-One3-TKL-QMK-Source.zip
```

See [release notes](docs/RELEASE_NOTES.md) for the changes in this package.
