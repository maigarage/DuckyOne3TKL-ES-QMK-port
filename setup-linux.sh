#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-2.0-or-later
set -euo pipefail
project_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
printf '%s\n' 'Ducky One 3 TKL RGB source setup — Debian 12/13 or Ubuntu 24.04 LTS, x86_64.'
printf '%s\n' 'Dependencies are installed non-interactively under their published licenses (see THIRD_PARTY.md).'
printf '%s\n' 'OS authentication through sudo may still be required. Nothing will be flashed by setup.'
read -r -p "Working directory [${HOME}/DuckyOne3]: " work_dir
work_dir="${work_dir:-${HOME}/DuckyOne3}"
case "$work_dir" in '~/'*) work_dir="$HOME/${work_dir:2}" ;; esac
if [[ "$work_dir" =~ [[:space:]] || "$work_dir" != /* ]]; then
    printf '%s\n' 'Use an absolute directory without whitespace (required by QMK make).' >&2; exit 1
fi
if [[ "$(uname -m)" != x86_64 ]] || ! command -v apt-get >/dev/null; then
    printf '%s\n' 'Automatic setup supports x86_64 Debian/Ubuntu with apt. See docs/BUILD.md for other systems.' >&2; exit 1
fi
mkdir -p -- "$work_dir"
work_dir="$(cd -- "$work_dir" && pwd)"
if [[ ! -e "$work_dir/.ducky-workspace" && -n "$(ls -A -- "$work_dir")" ]]; then
    printf '%s\n' 'Choose an empty directory or an existing Ducky workspace. Existing files were not changed.' >&2; exit 1
fi
touch "$work_dir/.ducky-workspace"
admin=()
if [[ $EUID != 0 ]]; then admin=(sudo); sudo -v; fi
"${admin[@]}" env DEBIAN_FRONTEND=noninteractive apt-get update
"${admin[@]}" env DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    ca-certificates git make gcc-arm-none-eabi binutils-arm-none-eabi libnewlib-arm-none-eabi \
    build-essential python3 python3-venv python3-dev python3-tk pkg-config \
    libhidapi-hidraw0 libhidapi-libusb0 libusb-1.0-0-dev libudev-dev udev
python3 -m venv "$work_dir/runtime"
"$work_dir/runtime/bin/python" -m pip install --disable-pip-version-check -r "$project_dir/requirements.txt"
"$work_dir/runtime/bin/python" -m unittest discover -s "$project_dir/tests" -v
# QMK's 'hid' package and the flasher's 'hidapi' package must stay isolated.
python3 -m venv "$work_dir/build-env"
"$work_dir/build-env/bin/python" -m pip install --disable-pip-version-check qmk==1.2.0
"${admin[@]}" install -m 0644 "$project_dir/scripts/70-ducky-one3.rules" /etc/udev/rules.d/70-ducky-one3.rules
"${admin[@]}" udevadm control --reload-rules
"${admin[@]}" udevadm trigger --subsystem-match=hidraw
"$work_dir/runtime/bin/python" "$project_dir/tools/prepare.py" "$work_dir"
PATH="$work_dir/build-env/bin:$PATH" "$work_dir/build-env/bin/python" "$project_dir/tools/build.py" "$work_dir" 2>&1 | tee "$work_dir/build.log"
"$work_dir/runtime/bin/python" "$project_dir/tools/finalize.py" "$work_dir"
"$work_dir/runtime/bin/python" -m pip freeze > "$work_dir/runtime-packages.txt"
"$work_dir/build-env/bin/python" -m pip freeze > "$work_dir/build-packages.txt"
"$work_dir/runtime/bin/python" "$project_dir/tools/license_inventory.py" "$work_dir/dependency-licenses/runtime"
"$work_dir/build-env/bin/python" "$project_dir/tools/license_inventory.py" "$work_dir/dependency-licenses/build"
dpkg-query -W > "$work_dir/system-packages.txt"
printf '#!/usr/bin/env bash\nset -euo pipefail\nexec %q %q --workspace %q "$@"\n' \
    "$work_dir/runtime/bin/python" "$project_dir/tools/manage.py" "$work_dir" > "$work_dir/Manage-Ducky.sh"
chmod +x "$work_dir/Manage-Ducky.sh"
printf '#!/usr/bin/env bash\nset -euo pipefail\nexec %q %q "$@"\n' \
    "$work_dir/runtime/bin/python" "$project_dir/tools/settings.py" > "$work_dir/Settings-Ducky.sh"
chmod +x "$work_dir/Settings-Ducky.sh"
printf '\nSettings (normal keyboard mode, close VIA): %s\n' "$work_dir/Settings-Ducky.sh"
printf '\nSetup completed. Start the graphical install/restore assistant:\n  %s\n' "$work_dir/Manage-Ducky.sh"
printf '%s\n' 'Keep this extracted source directory: the launcher uses its tools.'
