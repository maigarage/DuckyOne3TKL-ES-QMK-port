#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-2.0-or-later
set -euo pipefail
project_dir="$(cygpath -u "$DUCKY_PROJECT")"
work_dir="$(cygpath -u "$DUCKY_WORKSPACE")"
cd -- "$project_dir"
command -v arm-none-eabi-gcc
command -v qmk
python3 tools/build.py "$work_dir" 2>&1 | tee "$work_dir/build.log"
python3 tools/license_inventory.py "$work_dir/dependency-licenses/build"
if python3 -m pip --version >/dev/null 2>&1; then
    python3 -m pip freeze > "$work_dir/build-packages.txt"
else
    printf '%s\n' 'QMK MSYS manages Python tools separately; see msys-packages.txt and qmk version below.' > "$work_dir/build-packages.txt"
fi
qmk --version >> "$work_dir/build-packages.txt"
pacman -Q > "$work_dir/msys-packages.txt"
