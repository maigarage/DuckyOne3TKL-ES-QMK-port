#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Download, verify and extract local-only Ducky inputs; never flash a device."""
import argparse
import hashlib
import json
import os
import subprocess
import sys
import urllib.request
from pathlib import Path
from target import UPDATER_URL, UPDATER_SHA256


def download(url, destination, expected):
    if destination.exists() and hashlib.sha256(destination.read_bytes()).hexdigest() == expected:
        return
    request = urllib.request.Request(url, headers={"User-Agent": "DuckyOne3CommunityPort/1.0"})
    with urllib.request.urlopen(request, timeout=60) as response:
        data = response.read()
    if hashlib.sha256(data).hexdigest() != expected:
        raise ValueError("Download hash mismatch. Refusing to use changed vendor input.")
    temporary = destination.with_suffix(".part")
    temporary.write_bytes(data)
    os.replace(temporary, destination)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workspace", type=Path)
    args = parser.parse_args()
    work = args.workspace.resolve()
    vendor = work / "vendor"
    vendor.mkdir(parents=True, exist_ok=True)
    updater = vendor / "Ducky-One3-TKL-RGB-1.16.exe"
    print("Downloading/verifying Ducky's original updater (download only; never executed).", flush=True)
    download(UPDATER_URL, updater, UPDATER_SHA256)
    subprocess.run([sys.executable, str(Path(__file__).with_name("generate_vendor.py")), str(updater), str(vendor)], check=True)
    (work / "workspace.json").write_text(json.dumps({"schema": 1, "project": str(Path(__file__).resolve().parents[1]),
                                                   "python": sys.executable}, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
