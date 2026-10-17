#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Validate linked firmware and publish the local manifest only after passing."""
import argparse
import hashlib
import json
import os
import struct
from pathlib import Path
from elftools.elf.elffile import ELFFile
from flashing import candidate, image_packets, load_image
from target import EXPECTED, ORIGINAL_SHA256, STOCK_NAME, QMK_COMMIT


def verify(work):
    load_image(work / "vendor" / STOCK_NAME, ORIGINAL_SHA256)
    firmware = work / "firmware"
    binary = (firmware / "qmk.bin").read_bytes()
    candidate(EXPECTED, binary)
    with (firmware / "qmk.elf").open("rb") as stream:
        elf = ELFFile(stream)
        symbols = {s.name: int(s["st_value"]) for s in elf.get_section_by_name(".symtab").iter_symbols()}
        for segment in elf.iter_segments():
            if segment["p_type"] == "PT_LOAD" and segment["p_filesz"] and segment["p_paddr"] < 0x20000:
                start = int(segment["p_paddr"])
                if binary[start:start + segment["p_filesz"]] != segment.data():
                    raise ValueError("ELF and BIN do not describe the same loadable flash contents")
    if len(binary)>0x1e000:raise ValueError("Firmware overlaps settings partition")
    if not (0x20000000 <= symbols["flash_operation"] < 0x20005000):
        raise ValueError("Flash operation is not linked into SRAM")
    vectors = struct.unpack_from("<48I", binary)
    if vectors[0] != symbols["__main_stack_end__"]:
        raise ValueError("Stack vector does not match linked stack")
    for index in (1, 3, 15, 17, 25, 39):
        if not (vectors[index] & 1 and (vectors[index] & ~1) < len(binary)):
            raise ValueError(f"Invalid required interrupt vector {index}")
    for index, name in ((25, "Vector64"), (17, "Vector44")):
        if (vectors[index] & ~1) != (symbols[name] & ~1):
            raise ValueError(f"Wrong handler for vector {index}")
    if not (symbols["__bss_end__"] < 0x20005000 and symbols["__heap_base__"] < symbols["__heap_end__"]):
        raise ValueError("Linked RAM/heap exceeds the supported part")
    for name in ("ducky_safety_halt", "ducky_stock_blob", "ducky_stock_lut"):
        if name not in symbols:
            raise ValueError(f"Required firmware symbol absent: {name}")
    if bytes.fromhex("12 01 00 02 00 00 00 40 33 32 11 83 20 00") not in binary:
        raise ValueError("Unexpected USB device descriptor")
    return {"schema": 1, "sha256": hashlib.sha256(binary).hexdigest(), "bytes": len(binary),
            "qmk_commit": QMK_COMMIT, "packet_count": len(list(image_packets(binary))),
            "scope": "APROM code below 0x1e000; settings 0x1e000..0x1ffff", "baseline": "test10.5",
            "settings_schema": "0x000a0001", "settings_save": "explicit Save only; defaults reset changes RAM only", "hardware_validated": False,
            "ram_bytes_including_stacks": symbols["__bss_end__"] - 0x20000000}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workspace", type=Path)
    args = parser.parse_args()
    result = verify(args.workspace)
    path = args.workspace / "firmware" / "manifest.json"
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, path)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
