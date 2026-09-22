#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

RELEASES = {
    ("POKEMON_SLVAAXJ", 0): {"profile":"jp-rev0","release_id":"silver-jp-rev0","layout_family":"jp","language":"Japanese","rom_bytes":1048576,"sha256":"0a532063a3ff5750a464582aa7bbee2b6d42e1a92a136d9f4590e373487b615c"},
    ("POKEMON_SLVAAXJ", 1): {"profile":"jp-rev1","release_id":"silver-jp-rev1","layout_family":"jp","language":"Japanese","rom_bytes":1048576,"sha256":"99e5267fbf5a7748d4f3b75ba1990cb5d91348339468607a04bfbc6081c62d71"},
    ("POKEMON_SLVAAXK", 0): {"profile":"ko-rev0","release_id":"silver-ko-rev0","layout_family":"ko","language":"Korean","rom_bytes":2097152,"sha256":"ebbac63c0c4309c82dbb6723e7163369784f962b4fd3e2f486075307c3008a22"},
    ("POKEMON_SLVAAXE", 0): {"profile":"en-rev0","release_id":"silver-en-rev0","layout_family":"western","language":"English","rom_bytes":2097152,"sha256":"72b190859a59623cbef6c49d601f8de52c1d2331b4f08a8d2acc17274fc19a8c"},
    ("POKEMON_SLVAAXD", 0): {"profile":"de-rev0","release_id":"silver-de-rev0","layout_family":"western","language":"German","rom_bytes":2097152,"sha256":"c3d1fd0dec1d5fa9aa7f85275e79c52aa9175d191c63cbed7b406c306d946348"},
    ("POKEMON_SLVAAXF", 0): {"profile":"fr-rev0","release_id":"silver-fr-rev0","layout_family":"western","language":"French","rom_bytes":2097152,"sha256":"e120c4ddb0dc3e25b95c9c71b3ffd59ff57ce689cf4d79d04913ba59140c18c2"},
    ("POKEMON_SLVAAXI", 0): {"profile":"it-rev0","release_id":"silver-it-rev0","layout_family":"western","language":"Italian","rom_bytes":2097152,"sha256":"04c442246d1ae0ed6bf5e072bb7e3d06376e584b953d6b14047b39e45fbb0cb4"},
    ("POKEMON_SLVAAXS", 0): {"profile":"es-rev0","release_id":"silver-es-rev0","layout_family":"western","language":"Spanish","rom_bytes":2097152,"sha256":"6797010c052e8f9373ea2b9e855ec078b34fda12e5ccf742eb19bb5e8f6947c2"},
}

def decode_title(data: bytes) -> str:
    if len(data) < 0x150:
        raise ValueError("ROM is too small for a Game Boy header")
    return data[0x134:0x143].decode("ascii", "replace").rstrip("\0")

def detect_rom(data: bytes, *, require_baseline_hash: bool = False) -> dict:
    title = decode_title(data)
    revision = data[0x14C]
    try:
        release = RELEASES[(title, revision)]
    except KeyError as exc:
        raise ValueError(f"unsupported Silver release header: title={title!r} revision={revision}") from exc
    if data[0x147] != 0x10:
        raise ValueError(f"expected Silver cartridge type 0x10, got 0x{data[0x147]:02x}")
    if data[0x149] != 0x03:
        raise ValueError(f"expected Silver RAM size code 0x03, got 0x{data[0x149]:02x}")
    if len(data) != release["rom_bytes"]:
        raise ValueError(f"{release['profile']} ROM size mismatch: {len(data)} != {release['rom_bytes']}")
    digest = hashlib.sha256(data).hexdigest()
    hash_match = digest == release["sha256"]
    if require_baseline_hash and not hash_match:
        raise ValueError(f"{release['profile']} does not match the audited retail SHA-256")
    return {
        **release,
        "title": title,
        "revision": revision,
        "cartridge_type": data[0x147],
        "ram_size_code": data[0x149],
        "rom_sha256": digest,
        "baseline_sha256_match": hash_match,
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
        "sram_bank_sha256": [
            hashlib.sha256(core[i * 8192:(i + 1) * 8192]).hexdigest()
            for i in range(4)
        ] if len(core) == 32768 else [],
    }

def main() -> int:
    ap = argparse.ArgumentParser(description="Detect one of the eight audited retail Silver release profiles")
    ap.add_argument("rom", type=Path)
    ap.add_argument("--save", type=Path)
    ap.add_argument("--require-baseline-hash", action="store_true")
    ns = ap.parse_args()
    result = {"rom": detect_rom(ns.rom.read_bytes(), require_baseline_hash=ns.require_baseline_hash)}
    if ns.save:
        result["save"] = inspect_save(ns.save.read_bytes())
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
