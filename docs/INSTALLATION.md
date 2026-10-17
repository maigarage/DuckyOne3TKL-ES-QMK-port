# Installation and troubleshooting

Start with the platform steps in [README.md](../README.md). The source project
and generated build workspace are separate and both must remain available.
The setup scripts build the firmware; **Manage-Ducky** is the separate flashing
assistant. **Settings-Ducky** changes settings on an already running QMK keyboard.

## Upgrading to test10.5

This release changes the firmware, so rebuild and flash QMK. Extract the complete
new source package, run its Setup script, and select the existing build workspace
(e.g. `C:\DuckyOne3`). Setup reuses pinned dependencies and regenerates launchers
pointing at the new source directory. Keep that directory available afterward.
Then run Manage-Ducky and choose QMK installation. The 10-second bootloader wait
and explicit flashing confirmation remain in place.

Disconnect USB power once before starting the upgrade if the old firmware is
latched dark. Reconnect as instructed by Manage-Ducky for D+L bootloader entry.
Never disconnect during flashing. Existing saved settings use the same storage
schema; Restore defaults and Save are not required for this update.

A JSON import alone does not install this fix. The existing VIA control IDs remain
compatible; the bundled JSON identifies the new version. After installation,
follow the BIOS, shutdown and restart checks in [BIOS_USB.md](BIOS_USB.md).

## Windows troubleshooting

- **Setup window closes or a command fails:** run `Setup-Windows.cmd` from an open
  PowerShell window and retain its output. Compiler output is also in the
  workspace's `build.log`. A failed setup does not flash anything.
- **Workspace contains spaces:** choose a path such as `C:\DuckyOne3`, including
  when the Windows account's home directory contains spaces.
- **Downloaded scripts are blocked:** after verifying the package source, open
  the ZIP's Properties and use Unblock if Windows offers it, then extract again.
  Do not disable organization-managed security policy to run the tools.
- **Dependency installation asks for permission:** UAC is Windows authorization
  for the dependency installer. Keyboard flashing has its own later confirmation.
- **Existing QMK MSYS installation is incomplete:** repair that installation first;
  setup deliberately refuses to silently replace an inconsistent registered copy.
- **Wrong HID binding:** use the generated launcher and isolated runtime. QMK's
  Python environment and the flasher's `hidapi` environment are intentionally separate.
- **Keyboard is busy:** close VIA, other browser tabs using WebHID, Ducky's updater
  and other flashing assistants. Keep the existing HID driver.

Optional console interface from PowerShell:

```powershell
& 'C:\DuckyOne3\Manage-Ducky.cmd' --cli
```

It needs another keyboard (you can use On-Screen keyboard) while the Ducky is in bootloader mode. The GUI can be
operated with a mouse. Use the GUI's Cancel waiting button before programming;
console users can interrupt the pre-programming wait with Ctrl+C.

## Ubuntu troubleshooting

The documented automated path is Ubuntu 24.04 LTS x86_64 with a local desktop.
Setup also targets x86_64 Debian 12/13; other systems are not validated by this
package. See [BUILD.md](BUILD.md) for manual dependencies on other distributions.

- **No Tk window / no display:** use a local graphical session. A remote or headless
  session can use `--cli` only after the administrator grants appropriate HID access.
- **Permission denied opening HID:** setup installs `scripts/70-ducky-one3.rules`
  and reloads udev. Reconnect the keyboard and retry as the active local user.
  Do not use `chmod 666` or run the entire assistant as root to bypass permissions.
- **Dependencies fail to install:** retain the `apt`/`pip` error and resolve package
  availability, network or permissions before rerunning setup with the same workspace.
- **Build fails:** inspect `$HOME/DuckyOne3/build.log` (or your chosen workspace).
- **Launcher points to a missing source directory:** restore that directory or
  rerun setup from its new location using the same workspace.

Console interface:

```bash
"$HOME/DuckyOne3/Manage-Ducky.sh" --cli
```

## Bootloader and recovery

Enter bootloader mode by unplugging, holding D + L, and reconnecting. Detection
starts a 10-second wait after the device opens. Release the keys. The assistant
checks that exactly one matching bootloader with the selected HID path remains
present throughout the wait. If a disconnect or device-selection change is seen,
the attempt stops. A subsequent attempt starts a new full countdown.

After the wait, the chip/configuration and image are checked and confirmation is
requested. The countdown does not establish board identity, provide power-loss
protection or replace any of those checks.

If a flash transfer has already failed, recovery is selected automatically and
requires another confirmation. Keep the persistent recovery marker intact. Read
[SAFETY.md](SAFETY.md#interrupted-transfers) before retrying.

## VIA issues

- **Bootloader visible but VIA cannot configure it:** VIA needs the running QMK
  application, not D+L mode. Finish installation and wait for normal enumeration.
- **Changes disappear after unplugging:** changes are deliberately RAM-only until
  Settings storage → Keyboard flash → Save current settings to flash succeeds.
- **Defaults did not change after upgrading:** an existing saved snapshot takes
  priority. Restore defaults, review the result, and save if desired.
- **Status text appears stale:** reopen the settings menu or reconnect VIA.
- **FN does not appear as a normal key in a tester:** its layer action is handled
  inside QMK; test the keys it exposes on the corresponding layer.

For a useful issue report, include the OS, package revision, keyboard model,
selected action, exact error and relevant log excerpt. Remove personal paths or
other unrelated information before publishing logs.
