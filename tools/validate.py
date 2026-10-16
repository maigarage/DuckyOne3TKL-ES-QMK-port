#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Run current firmware emulation tests in an isolated, local-only staging tree."""
import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from target import KEYBOARD, STOCK_NAME


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workspace", type=Path)
    args = parser.parse_args()
    project = Path(__file__).resolve().parents[1]
    work = args.workspace.resolve()
    run = work / "validation-run"
    run.mkdir(parents=True, exist_ok=True)
    validation = run / "validation"
    shutil.copytree(project / "tests" / "firmware", validation, dirs_exist_ok=True)
    shutil.copytree(project / "source-overlay", run / "source-overlay", dirs_exist_ok=True)
    board = run / "source-overlay" / "keyboards" / KEYBOARD
    for name in ("ducky_stock_blob.S", "ducky_stock_initial.inc"):
        shutil.copy2(work / "vendor" / "generated" / name, board / name)
    (run / "analysis").mkdir(exist_ok=True)
    for name in (STOCK_NAME, "stock-engine-initial.bin"):
        shutil.copy2(work / "vendor" / name, run / "analysis" / name)
    (run / "firmware").mkdir(exist_ok=True)
    for name in ("qmk.bin", "qmk.elf"):
        shutil.copy2(work / "firmware" / name, run / "firmware" / name)

    def command(cmd, output=None):
        print("Running:", " ".join(map(str, cmd)), flush=True)
        result = subprocess.run(list(map(str, cmd)), cwd=run, check=True, text=True,
                                stdout=subprocess.PIPE if output else None)
        if output:
            (validation / output).write_text(result.stdout, encoding="utf-8")
            print(result.stdout, flush=True)

    command(["arm-none-eabi-gcc", "-mcpu=cortex-m0", "-mthumb", "-Os", "-g", "-DVIA_ENABLE",
             "-Ivalidation", "-I" + str(board), "-nostdlib", "-Wl,-T,validation/test.ld",
             *[board / name for name in ("caps_indicator.c", "ducky_stock.c", "ducky_stock_blob.S", "ducky_safety.c", "ducky_safety_asm.S")],
             "validation/settings_stubs.c", "-lc", "-lgcc", "-o", "validation/rgb.elf"])
    for section, filename in ((".text", "rgb-text.bin"), (".data", "rgb-data.bin")):
        command(["arm-none-eabi-objcopy", "-O", "binary", "-j", section, "validation/rgb.elf", "validation/" + filename])
    command(["arm-none-eabi-nm", "-n", "validation/rgb.elf"], "rgb.nm")
    for name in ("test_rgb", "test_linked_safety", "test_linked_settings", "test_flash_backend", "test_lut", "compare_stock_engine"):
        command([sys.executable, "validation/" + name + ".py"], name + ".json")
    command(["cc", "-std=c11", "-Wall", "-Wextra", "-Werror", "-Ivalidation/mouse", "-I" + str(board),
             "validation/mouse/test_mouse.c", board / "ducky_mouse.c", "-o", "validation/mouse-test"])
    command([str(validation / "mouse-test")], "mouse.txt")
    command(["cc", "-std=c11", "-Wall", "-Wextra", "-Werror", "-O2", "-I" + str(board),
             project / "tests/storage/test_store.c", board / "ducky_store.c", "-o", "validation/storage-test"])
    command([str(validation / "storage-test")], "storage.txt")
    if sys.platform.startswith("linux"):
        controller = project / "tests/persistence"
        command(["cc", "-std=c11", "-Wall", "-Wextra", "-Werror", "-O2",
                 "-I" + str(controller), "-I" + str(board), controller / "test_persistence.c",
                 board / "ducky_persistence.c", board / "ducky_store.c", "-o", "validation/persistence-test"])
        for case in range(16):
            command([str(validation / "persistence-test"), str(case)], f"persistence-{case}.txt")
    else:
        print("POSIX persistence-controller harness skipped: run this suite on Linux too.")
    print("All current firmware checks passed. These are software tests, not electrical certification.")


if __name__ == "__main__":
    main()
