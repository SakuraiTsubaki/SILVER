#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

TITLE_TO_PROFILE = {
    "POKEMON_SLVAAXJ": "jp",
    "POKEMON_SLVAAXK": "ko",
    "POKEMON_SLVAAXE": "western",
    "POKEMON_SLVAAXD": "western",
    "POKEMON_SLVAAXF": "western",
    "POKEMON_SLVAAXI": "western",
    "POKEMON_SLVAAXS": "western",
}

def decode_title(data: bytes) -> str:
    if len(data) < 0x150:
        raise ValueError("ROM is too small for a Game Boy header")
    return data[0x134:0x143].decode("ascii", "replace").rstrip("\0")

def detect_rom(data: bytes) -> dict:
    title = decode_title(data)
    profile = TITLE_TO_PROFILE.get(title)
    if profile is None:
        raise ValueError(f"unsupported Silver ROM title: {title!r}")
    cart_type = data[0x147]
    ram_size = data[0x149]
    if cart_type != 0x10:
        raise ValueError(f"expected Silver cartridge type 0x10, got 0x{cart_type:02x}")
    if ram_size != 0x03:
        raise ValueError(f"expected Silver RAM size code 0x03, got 0x{ram_size:02x}")
    return {
        "profile": profile,
        "title": title,
        "revision": data[0x14C],
        "rom_bytes": len(data),
        "cartridge_type": cart_type,
        "ram_size_code": ram_size,
        "sha256": hashlib.sha256(data).hexdigest(),
    }

def inspect_save(data: bytes) -> dict:
    if len(data) < 32768:
        raise ValueError("save is smaller than the complete 32 KiB Silver SRAM image")
    core = data[:32768]
    tail = data[32768:]
    return {
        "file_bytes": len(data),
        "raw_sram_bytes": len(core),
        "trailing_host_bytes": len(tail),
        "raw_sram_sha256": hashlib.sha256(core).hexdigest(),
        "trailing_host_sha256": hashlib.sha256(tail).hexdigest() if tail else None,
    }

def main() -> int:
    ap = argparse.ArgumentParser(description="Detect a retail Silver legacy ROM/save profile")
    ap.add_argument("rom", type=Path)
    ap.add_argument("--save", type=Path)
    ns = ap.parse_args()

    result = {"rom": detect_rom(ns.rom.read_bytes())}
    if ns.save:
        result["save"] = inspect_save(ns.save.read_bytes())
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
