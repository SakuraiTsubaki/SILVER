#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CONFIG=ROOT/"config"/"expansion.json"
BASELINE=ROOT/"analysis"/"rom-save-baseline.json"
PROFILES=ROOT/"config"/"legacy_save_profiles.json"
XMON=ROOT/"config"/"expanded_mon_v1.json"

EXPECTED=("jp-rev0","jp-rev1","ko-rev0","en-rev0","de-rev0","fr-rev0","it-rev0","es-rev0")

def load(path:Path):
    return json.loads(path.read_text(encoding="utf-8"))

def main()->int:
    cfg=load(CONFIG); baseline=load(BASELINE); profiles=load(PROFILES); xmon=load(XMON)

    if cfg.get("target_generation")!=10 or not cfg.get("forward_compatible"):
        raise SystemExit("Generation 10 forward-compatible target is required")
    if cfg["runtime"].get("platform")!="Game Boy Advance" or cfg["runtime"].get("legacy_gbc_runtime") is not False:
        raise SystemExit("SILVER runtime must remain GBA; legacy GBC structures are import/reference data")

    for key in ("species","form","move","item","ability"):
        if cfg["id_widths"].get(key,0)<16:
            raise SystemExit(f"{key} ID must be at least 16-bit")

    releases=baseline["releases"]
    if baseline.get("release_count")!=8 or len(releases)!=8:
        raise SystemExit("exactly eight audited Silver release pairs are required")
    ids=tuple(r["profile_id"] for r in releases)
    if ids!=EXPECTED:
        raise SystemExit(f"release order/identity mismatch: {ids}")
    if any(not r["rom"]["header_checksum_valid"] or not r["rom"]["global_checksum_valid"] for r in releases):
        raise SystemExit("all audited ROM checksums must remain valid")
    if any(r["rom"]["cartridge_type"]!=0x10 or r["rom"]["ram_size_code"]!=0x03 for r in releases):
        raise SystemExit("all audited legacy ROMs must preserve MBC3+RTC+32KiB SRAM evidence")
    if any(r["save"]["raw_sram_bytes"]!=32768 or r["save"]["host_tail_bytes"]!=44 for r in releases):
        raise SystemExit("all eight supplied saves must preserve 32KiB SRAM + 44-byte observed tail evidence")
    if any(len(r["save"]["sram_bank_sha256"])!=4 for r in releases):
        raise SystemExit("all save baselines must retain four independent SRAM bank hashes")

    p=profiles["profiles"]
    if tuple(p)!=EXPECTED or profiles.get("profile_count")!=8:
        raise SystemExit("legacy save profiles must preserve all eight release identities")
    if any(p[k]["profile_code"]!=i+1 for i,k in enumerate(EXPECTED)):
        raise SystemExit("release profile codes are not stable")
    if any(p[k]["layout_family"]=="western" and k=="western" for k in p):
        raise SystemExit("western must never be a release profile")
    if (p["jp-rev0"]["boxes"],p["jp-rev0"]["mons_per_box"])!=(9,30):
        raise SystemExit("Japanese layout evidence changed")
    if (p["jp-rev1"]["boxes"],p["jp-rev1"]["mons_per_box"])!=(9,30):
        raise SystemExit("Japanese Rev A layout evidence changed")
    for k in EXPECTED[2:]:
        if (p[k]["boxes"],p[k]["mons_per_box"])!=(14,20):
            raise SystemExit(f"{k} layout evidence changed")

    save=cfg["save"]
    if tuple(save.get("legacy_profiles",[]))!=EXPECTED or save.get("legacy_profile_count")!=8:
        raise SystemExit("runtime import list must include all eight release profiles")
    if not save.get("release_identity_preserved") or not save.get("legacy_import_is_read_only"):
        raise SystemExit("release provenance and read-only legacy import are mandatory")

    if xmon["profile_codes"]!={k:i+1 for i,k in enumerate(EXPECTED)}:
        raise SystemExit("ExpandedMonV1 must encode all eight exact release profiles")
    if xmon.get("record_bytes")!=64 or xmon.get("legacy_box_record_bytes")!=32:
        raise SystemExit("ExpandedMonV1 size contract changed")
    if xmon["migration_defaults"]["form_id"]!=0 or xmon["migration_defaults"]["ability_id"]!=0:
        raise SystemExit("legacy migration must not infer form or ability")

    print("SILVER all-release Generation-10 expansion contract: OK")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
