#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Package the public source tree, never the private workspace or vendor outputs."""
import argparse
import hashlib
import json
import zipfile
from pathlib import Path

ROOT_FILES = {"README.md", "LICENSE", "NOTICE", "THIRD_PARTY.md", ".gitignore", ".gitattributes",
              "requirements.txt", "Setup-Windows.cmd", "Setup-Windows.ps1", "setup-linux.sh"}
DIRECTORIES = {"source-overlay", "tools", "scripts", "docs", "tests", "research", "via", "licenses", ".github"}
EXTENSIONS = {".md", ".txt", ".py", ".c", ".h", ".S", ".mk", ".ld", ".json", ".sh", ".ps1", ".cmd", ".rules", ".yml"}
FORBIDDEN = {"ducky_stock_blob.S", "ducky_stock_initial.inc"}


def files(root):
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if not path.is_file() or "__pycache__" in relative.parts or path.suffix == ".pyc":
            continue
        if str(relative) not in ROOT_FILES and relative.parts[0] not in DIRECTORIES:
            continue
        if path.is_symlink() or path.name in FORBIDDEN:
            raise ValueError(f"Refusing generated/vendor input or symlink: {relative}")
        if str(relative) not in ROOT_FILES and path.suffix not in EXTENSIONS:
            raise ValueError(f"Unexpected public artifact: {relative}")
        yield path, relative


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    output = args.output.resolve()
    if output.is_relative_to(root):
        raise ValueError("Write the ZIP outside the source tree")
    entries = list(files(root))
    output.parent.mkdir(parents=True, exist_ok=True)
    hashes = {str(rel).replace("\\", "/"): hashlib.sha256(path.read_bytes()).hexdigest() for path, rel in entries}
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path, relative in entries:
            archive.write(path, "ducky-one3-tkl-qmk/" + relative.as_posix())
        archive.writestr("ducky-one3-tkl-qmk/SOURCE_SHA256.json", json.dumps(hashes, indent=2) + "\n")
    print(json.dumps({"file": str(output), "source_files": len(entries), "bytes": output.stat().st_size,
                      "sha256": hashlib.sha256(output.read_bytes()).hexdigest()}, indent=2))


if __name__ == "__main__":
    main()
