#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Get pinned QMK sources, apply the complete overlay, compile, validate and stage."""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from target import QMK_COMMIT, KEYBOARD, QMK_ARTIFACT
import sources

PROJECT = Path(__file__).resolve().parents[1]


def run(args, cwd=None, capture=False):
    print("Running:", " ".join(map(str, args)), flush=True)
    return subprocess.run(list(map(str, args)), cwd=cwd, check=True, text=True,
                          stdout=subprocess.PIPE if capture else None).stdout


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workspace", type=Path)
    parser.add_argument("--source", type=Path, help="Developer option: explicit existing QMK checkout to overlay")
    args = parser.parse_args()
    work = args.workspace.resolve()
    source = args.source.resolve() if args.source else work / "qmk"
    if any(c.isspace() for c in str(source)):
        raise ValueError("QMK make requires a workspace path without whitespace")
    if not args.source:
        sources.prepare(source)
    if run(["git", "rev-parse", "HEAD"], source, True).strip() != QMK_COMMIT:
        raise RuntimeError("QMK checkout is at another commit. No reset/overwrite performed.")
    overlay_hashes = {}
    for path in (PROJECT / "source-overlay").rglob("*"):
        if path.is_file():
            target = source / path.relative_to(PROJECT / "source-overlay")
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, target)
            overlay_hashes[target] = hashlib.sha256(path.read_bytes()).digest()
    for name in ("ducky_stock_blob.S", "ducky_stock_initial.inc"):
        shutil.copy2(work / "vendor" / "generated" / name, source / "keyboards" / KEYBOARD / name)
    # Fresh firmware build: stale successful output must never be staged after failure.
    run(["make", "clean", "SKIP_GIT=yes"], source)
    run(["make", f"{KEYBOARD}:via", "SKIP_GIT=yes", f"-j{min(os.cpu_count() or 2, 8)}"], source)
    for path, expected in overlay_hashes.items():
        if hashlib.sha256(path.read_bytes()).digest() != expected:
            raise RuntimeError(f"Overlay source changed during build; no firmware staged: {path}")
    firmware = work / "firmware"
    firmware.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source / f"{QMK_ARTIFACT}.bin", firmware / "qmk.bin")
    shutil.copy2(source / ".build" / f"{QMK_ARTIFACT}.elf", firmware / "qmk.elf")
    mapfile = source / ".build" / f"{QMK_ARTIFACT}.map"
    if mapfile.exists():
        shutil.copy2(mapfile, firmware / "qmk.map")
    # Native host Python has pyelftools; MSYS build reports are completed by finalize.py.
    report = {"qmk_commit": QMK_COMMIT, "compiler": run(["arm-none-eabi-gcc", "--version"], capture=True).splitlines()[0],
              "dependencies": sources.provenance(source),
              "binary_sha256": hashlib.sha256((firmware / "qmk.bin").read_bytes()).hexdigest()}
    (firmware / "build-provenance.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("Build staged. Run finalize.py before using the flashing assistant.")


if __name__ == "__main__":
    main()
