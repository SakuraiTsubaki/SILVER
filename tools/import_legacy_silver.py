#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from tools.decode_legacy_save import decode_legacy_save, load_layouts
from tools.detect_legacy_profile import detect_rom

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_AUDIT = ROOT / "analysis" / "save-structure-audit.json"

def load_audited_save_hashes(path: Path = DEFAULT_AUDIT) -> dict[str, str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return {entry["profile_id"]: entry["save_sha256"] for entry in data["profiles"]}

def import_legacy_pair(
    rom: bytes,
    save: bytes,
    *,
    require_retail_rom: bool = True,
    require_primary_save_valid: bool = True,
    layouts: dict[str, Any] | None = None,
    audited_save_hashes: dict[str, str] | None = None,
) -> dict[str, Any]:
    rom_info = detect_rom(rom, require_baseline_hash=require_retail_rom)
    profile = rom_info["profile"]
    decoded = decode_legacy_save(save, profile=profile, layouts=layouts or load_layouts())

    primary = decoded["primary_save"]
    primary_valid = (
        primary["checksum_valid"]
        and primary["check_value_1_valid"]
        and primary["check_value_2_valid"]
    )
    if require_primary_save_valid and not primary_valid:
        raise ValueError(f"{profile} SAV failed primary save validation")

    audited_save_hashes = audited_save_hashes or load_audited_save_hashes()
    save_sha256 = hashlib.sha256(save).hexdigest()

    return {
        "schema_version": 1,
        "source": {
            "profile_id": profile,
            "release_id": rom_info["release_id"],
            "language": rom_info["language"],
            "layout_family": rom_info["layout_family"],
            "rom_sha256": rom_info["rom_sha256"],
            "retail_rom_sha256_match": rom_info["baseline_sha256_match"],
            "save_sha256": save_sha256,
            "supplied_audit_sample_save_match": audited_save_hashes.get(profile) == save_sha256,
            "primary_save_valid": primary_valid,
        },
        "gba_import": decoded["normalized_gba_import"],
        "legacy_summary": {
            "party_count": decoded["party"]["count"],
            "active_box_count": decoded["active_box"]["count"],
            "stored_box_counts": [box["count"] for box in decoded["stored_boxes"]],
            "raw_sram_sha256": decoded["raw_sram_sha256"],
            "host_tail_bytes": decoded["host_tail_bytes"],
        },
    }

def main() -> int:
    ap = argparse.ArgumentParser(
        description="Pair a Silver ROM with its SAV and emit the normalized GBA import model"
    )
    ap.add_argument("rom", type=Path)
    ap.add_argument("save", type=Path)
    ap.add_argument("-o", "--output", type=Path)
    ap.add_argument(
        "--allow-modified-rom",
        action="store_true",
        help="allow a header-compatible ROM whose SHA-256 is not the audited retail baseline",
    )
    ap.add_argument(
        "--allow-invalid-primary-save",
        action="store_true",
        help="decode even when the primary checksum/check values fail",
    )
    ns = ap.parse_args()
    payload = import_legacy_pair(
        ns.rom.read_bytes(),
        ns.save.read_bytes(),
        require_retail_rom=not ns.allow_modified_rom,
        require_primary_save_valid=not ns.allow_invalid_primary_save,
    )
    rendered = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if ns.output:
        ns.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
