#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CONFIG=ROOT/"config"/"expansion.json"
BASELINE=ROOT/"analysis"/"rom-save-baseline.json"
PROFILES=ROOT/"config"/"legacy_save_profiles.json"
XMON=ROOT/"config"/"expanded_mon_v1.json"

def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))

def main() -> int:
    cfg=load(CONFIG)
    baseline=load(BASELINE)
    profiles=load(PROFILES)
    xmon=load(XMON)

    if cfg.get("target_generation") != 10 or not cfg.get("forward_compatible"):
        raise SystemExit("Generation 10 forward-compatible target is required")

    for key in ("species","form","move","item","ability"):
        if cfg["id_widths"].get(key,0) < 16:
            raise SystemExit(f"{key} ID must be at least 16-bit")

    roms=baseline["roms"]
    if len(roms) != 8:
        raise SystemExit("expected eight observed Silver ROM identities")
    if any(x["cartridge_type"] != 0x10 for x in roms):
        raise SystemExit("observed Silver ROMs must retain MBC3+timer+RAM+battery evidence")
    if any(x["ram_size_code"] != 0x03 for x in roms):
        raise SystemExit("observed Silver ROMs must declare 32 KiB SRAM")

    saves=baseline["saves"]
    if len(saves) != 8:
        raise SystemExit("expected eight observed Silver save files")
    if any(x["raw_sram_bytes"] != 32768 for x in saves):
        raise SystemExit("legacy raw SRAM size must remain 32 KiB")
    if any(x["host_tail_bytes"] != 44 for x in saves):
        raise SystemExit("observed save wrapper tail must remain recorded as 44 bytes")

    p=profiles["profiles"]
    if set(p) != {"jp","ko","western"}:
        raise SystemExit("JP, KO and Western legacy save profiles are all required")
    if (p["jp"]["boxes"],p["jp"]["mons_per_box"],p["jp"]["hall_of_fame_teams"]) != (9,30,50):
        raise SystemExit("Japanese save profile does not match source-confirmed layout")
    for key in ("ko","western"):
        if (p[key]["boxes"],p[key]["mons_per_box"],p[key]["hall_of_fame_teams"]) != (14,20,30):
            raise SystemExit(f"{key} save profile does not match source-confirmed layout")

    save=cfg["save"]
    if not save.get("migration_required") or not save.get("legacy_import_is_read_only"):
        raise SystemExit("legacy save import must be explicit and read-only")
    if save.get("legacy_profiles") != ["jp","ko","western"]:
        raise SystemExit("expansion config must bind all three legacy profiles")

    rom=cfg["rom"]
    if rom.get("legacy_cartridge_type") != 0x10:
        raise SystemExit("legacy cartridge type must be 0x10")
    if rom.get("native_mbc3_rom_bank_ceiling") != 128:
        raise SystemExit("native MBC3 ceiling must remain explicit")
    if not rom.get("require_rtc_preservation") or not rom.get("require_mapper_abstraction"):
        raise SystemExit("RTC-preserving mapper abstraction is required")

    far=cfg["far_pointer"]
    if far.get("logical_bank_bits",0) < 16 or far.get("offset_bits",0) < 16 or far.get("serialized_bytes") != 4:
        raise SystemExit("extended far pointer ABI must be 16-bit bank + 16-bit offset")

    if xmon.get("record_bytes") != 64 or xmon.get("legacy_box_record_bytes") != 32:
        raise SystemExit("ExpandedMonV1 must remain 64 bytes over a 32-byte legacy box record")
    if xmon["migration_defaults"] != {
        "form_id": 0,
        "ability_id": 0,
        "note": "Legacy Silver does not encode modern form or ability identities; migration must not infer them."
    }:
        raise SystemExit("legacy migration must not infer form or ability")
    fields={field["name"]:(field["offset"],field["bytes"]) for field in xmon["fields"]}
    expected={
        "species_id":(0,2),"form_id":(2,2),"item_id":(4,2),"ability_id":(6,2),
        "move_ids":(8,8),"legacy_tail":(16,26),"source_profile":(42,1),
        "source_revision":(43,1),"feature_flags":(44,4),"reserved":(48,16)
    }
    if fields != expected:
        raise SystemExit("ExpandedMonV1 field layout changed without an ABI version change")

    print("SILVER ROM/save-driven expansion contract: OK")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
