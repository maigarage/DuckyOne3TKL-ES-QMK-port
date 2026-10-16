# SPDX-License-Identifier: GPL-2.0-or-later
"""Pinned, shallow, blob-filtered sparse checkouts for this one firmware target.

Each dependency is an independent checkout at the pinned QMK gitlink. No recursive
submodule update can pull in demos, unrelated MCUs or other keyboards.
"""
import json
import configparser
import re
import subprocess
from pathlib import Path
from target import QMK_COMMIT

SOURCES = [
    (".", "https://github.com/qmk/qmk_firmware.git", QMK_COMMIT,
     ["builddefs", "data", "drivers", "lib/python", "platforms/chibios",
      "quantum", "tmk_core", "util"]),
    ("lib/chibios", "https://github.com/qmk/ChibiOS.git", "6170ddf92d55be54c89b708d1882eea229edeb2c",
     ["os/license", "os/common/portability/GCC", "os/common/oop", "os/common/startup/ARMCMx/compilers/GCC", "os/common/ports/ARMv6-M",
      "os/common/ports/ARMCMx", "os/common/ports/ARM-common", "os/common/ext/CMSIS/include", "os/common/ext/ARM/CMSIS/Core/Include",
      "os/hal/include", "os/hal/src", "os/hal/osal/rt-nil", "os/hal/lib/streams",
      "os/hal/ports/common/ARMCMx", "os/oslib", "os/rt", "os/various/newlib_bindings"]),
    ("lib/chibios-contrib", "https://github.com/qmk/ChibiOS-Contrib.git", "5a9ad82b6ba4f649cdb800e8c2bbc9be2d3ce767",
     ["os/common/startup/ARMCMx/compilers/GCC", "os/common/startup/ARMCMx/devices/NUC123",
      "os/common/ext/CMSIS/Nuvoton/NUMICRO", "os/hal/ports/NUMICRO", "os/hal/include", "os/hal/src"]),
    ("lib/lufa", "https://github.com/qmk/lufa.git", "549b97320d515bfca2f95c145a67bd13be968faa",
     ["LUFA/Common", "LUFA/Drivers/USB/Class/Common", "LUFA/Drivers/USB/Core"]),
    ("lib/printf", "https://github.com/qmk/printf.git", "c2e3b4e10d281e7f0f694d3ecbd9f320977288cc",
     ["src"]),
]


def git(path, *args, capture=False, check=True):
    print("Git:", path, *args, flush=True)
    return subprocess.run(["git", "-C", str(path), *args], check=check, text=True,
                          stdout=subprocess.PIPE if capture else None,
                          stderr=subprocess.PIPE if capture else None)


def metadata_directory(path):
    metadata = Path(path) / ".git"
    if metadata.is_file():
        text = metadata.read_text().strip()
        if not text.startswith("gitdir: "):
            raise RuntimeError(f"Invalid gitdir reference: {metadata}")
        metadata = (Path(path) / text[8:]).resolve()
    return metadata


def revision_at(path):
    """Inspect local checkout metadata without spawning Git or touching work files."""
    metadata = metadata_directory(path)
    head = (metadata / "HEAD").read_text().strip()
    if head.startswith("ref: "):
        ref = head[5:]
        if not ref.startswith("refs/") or ".." in Path(ref).parts:
            raise RuntimeError("Unexpected HEAD reference")
        loose = metadata / ref
        if loose.exists():
            head = loose.read_text().strip()
        else:
            packed = metadata / "packed-refs"
            head = next((line.split()[0] for line in packed.read_text().splitlines()
                         if line.endswith(" " + ref)), "") if packed.exists() else ""
    if not head:
        return None  # Interrupted initial fetch / unborn repository.
    if not re.fullmatch(r"[0-9a-f]{40}", head):
        raise RuntimeError(f"Invalid source revision metadata: {path}")
    return head


def checkout(path, url, revision, directories):
    path = Path(path)
    if not (path / ".git").exists():
        if path.exists() and any(path.iterdir()):
            raise RuntimeError(f"Refusing to overwrite nonempty source directory: {path}")
        path.mkdir(parents=True, exist_ok=True)
        git(path, "init")
        git(path, "remote", "add", "origin", url)
    config = configparser.ConfigParser(interpolation=None)
    config.read(metadata_directory(path) / "config", encoding="utf-8")
    actual = config.get('remote "origin"', "url", fallback="").strip()
    if actual.rstrip("/").removesuffix(".git") != url.removesuffix(".git"):
        raise RuntimeError(f"Unexpected source origin for {path}; no changes made")
    head = revision_at(path)
    if head:
        if head != revision:
            raise RuntimeError(f"Unexpected revision in {path}; no reset performed")
        # Existing complete or sparse checkouts may contain local edits; keep them.
        # The reduced layout is applied only before the first checkout.
        print("Reusing verified source checkout:", path, flush=True)
        return
    git(path, "config", "core.autocrlf", "false")
    git(path, "config", "remote.origin.promisor", "true")
    git(path, "config", "remote.origin.partialclonefilter", "blob:none")
    git(path, "sparse-checkout", "set", "--cone", *directories)
    git(path, "fetch", "--depth", "1", "--filter=blob:none", "--no-tags", "origin", revision)
    git(path, "checkout", "--detach", revision)
    if revision_at(path) != revision:
        raise RuntimeError(f"Source revision verification failed: {path}")


def prepare(root):
    root = Path(root)
    for relative, url, revision, directories in SOURCES:
        checkout(root / relative, url, revision, directories)
    # Local overlay supplies our only keyboard. No upstream keyboard blobs needed.
    for name in ("keyboards", "layouts", "users"):
        (root / name).mkdir(exist_ok=True)


def provenance(root):
    return [{"path": relative, "url": url,
             "revision": revision_at(Path(root) / relative),
             "requested_sparse_directories": directories}
            for relative, url, revision, directories in SOURCES]
