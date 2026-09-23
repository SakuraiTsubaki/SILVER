#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CONFIG=ROOT/"config"/"expansion.json"
BASELINE=ROOT/"analysis"/"rom-save-baseline.json"
PROFILES=ROOT/"config"/"legacy_save_profiles.json"
LAYOUTS=ROOT/"config"/"legacy_save_layouts.json"
SAVE_AUDIT=ROOT/"analysis"/"save-structure-audit.json"
GBA_IMPORT=ROOT/"config"/"gba_save_import_v1.json"
XMON=ROOT/"config"/"expanded_mon_v1.json"
EXPECTED=("jp-rev0","jp-rev1","ko-rev0","en-rev0","de-rev0","fr-rev0","it-rev0","es-rev0")
EXPECTED_CHECKSUMS={"jp-rev0":0x8FD3,"jp-rev1":0x9048,"ko-rev0":0x988D,"en-rev0":0xACF7,"de-rev0":0xAD24,"fr-rev0":0xBA45,"it-rev0":0xAB5E,"es-rev0":0xBA94}

def load(path:Path):
    return json.loads(path.read_text(encoding="utf-8"))

def main()->int:
    cfg=load(CONFIG); baseline=load(BASELINE); profiles=load(PROFILES)
    layouts=load(LAYOUTS); audit=load(SAVE_AUDIT); gba_import=load(GBA_IMPORT); xmon=load(XMON)
    if cfg.get("target_generation")!=10 or not cfg.get("forward_compatible"):
        raise SystemExit("Generation 10 forward-compatible target is required")
    if cfg["runtime"].get("platform")!="Game Boy Advance" or cfg["runtime"].get("legacy_gbc_runtime") is not False:
        raise SystemExit("SILVER runtime must remain GBA; legacy GBC structures are import/reference data")
    for key in ("species","form","move","item","ability"):
        if cfg["id_widths"].get(key,0)<16:
            raise SystemExit(f"{key} ID must be at least 16-bit")

    releases=baseline["releases"]
    if baseline.get("release_count")!=8 or tuple(r["profile_id"] for r in releases)!=EXPECTED:
        raise SystemExit("exactly eight audited Silver release pairs are required")
    if any(not r["rom"]["header_checksum_valid"] or not r["rom"]["global_checksum_valid"] for r in releases):
        raise SystemExit("all audited ROM checksums must remain valid")
    if any(r["rom"]["cartridge_type"]!=0x10 or r["rom"]["ram_size_code"]!=0x03 for r in releases):
        raise SystemExit("all audited legacy ROMs must preserve MBC3+RTC+32KiB SRAM evidence")
    if any(r["save"]["raw_sram_bytes"]!=32768 or r["save"]["host_tail_bytes"]!=44 for r in releases):
        raise SystemExit("all eight supplied saves must preserve 32KiB SRAM + 44-byte observed tail evidence")

    p=profiles["profiles"]
    if tuple(p)!=EXPECTED or profiles.get("profile_count")!=8:
        raise SystemExit("legacy save profiles must preserve all eight release identities")
    if any(k in p for k in ("jp","ko","western")):
        raise SystemExit("family names must never replace exact release profiles")

    save=cfg["save"]
    if tuple(save.get("legacy_profiles",[]))!=EXPECTED or save.get("legacy_profile_count")!=8:
        raise SystemExit("runtime import list must include all eight release profiles")
    if not save.get("release_identity_preserved") or not save.get("legacy_import_is_read_only"):
        raise SystemExit("release provenance and read-only legacy import are mandatory")

    lp=layouts.get("profiles",{})
    if tuple(lp)!=EXPECTED:
        raise SystemExit("save decoder layouts must include exactly eight release profiles")
    for key in ("jp-rev0","jp-rev1"):
        l=lp[key]
        if (l["party"]["file_offset"],l["party"]["bytes"],l["active_box"]["file_offset"],l["active_box"]["bytes"],l["stored_boxes"]["box_bytes"],l["stored_boxes"]["count"],l["primary_checksum"]["stored_offset"])!=(0x283E,0x170,0x2D10,0x548,0x54A,9,0x2D0D):
            raise SystemExit(f"{key} save geometry changed")
    ko=lp["ko-rev0"]
    if (ko["party"]["file_offset"],ko["active_box"]["file_offset"],ko["primary_checksum"]["stored_offset"])!=(0x28CC,0x2DAE,0x2DAB):
        raise SystemExit("Korean save geometry changed")
    for key in ("en-rev0","de-rev0","fr-rev0","it-rev0","es-rev0"):
        l=lp[key]
        if (l["party"]["file_offset"],l["active_box"]["file_offset"],l["primary_checksum"]["stored_offset"],l["stored_boxes"]["count"])!=(0x288A,0x2D6C,0x2D69,14):
            raise SystemExit(f"{key} localized save geometry changed")

    audited=audit.get("profiles",[])
    if audit.get("profile_count")!=8 or tuple(x["profile_id"] for x in audited)!=EXPECTED:
        raise SystemExit("save structure audit must cover all eight supplied SAVs")
    for entry in audited:
        pid=entry["profile_id"]; primary=entry["primary_checksum"]
        if primary["computed"]!=EXPECTED_CHECKSUMS[pid] or primary["stored"]!=EXPECTED_CHECKSUMS[pid]:
            raise SystemExit(f"{pid} audited primary checksum changed")
        if not primary["valid"] or not primary["check_value_1_valid"] or not primary["check_value_2_valid"]:
            raise SystemExit(f"{pid} supplied save no longer validates against the audited layout")
        if not entry["party"]["terminator_valid"] or not entry["active_box"]["terminator_valid"] or not entry["stored_boxes"]["all_terminators_valid"]:
            raise SystemExit(f"{pid} supplied party/box terminator audit failed")

    if tuple(gba_import.get("source_profiles",[]))!=EXPECTED or gba_import.get("runtime_platform")!="Game Boy Advance" or not gba_import.get("source_profile_is_required"):
        raise SystemExit("GBA import model must preserve all eight source profiles")
    if xmon["profile_codes"]!={k:i+1 for i,k in enumerate(EXPECTED)}:
        raise SystemExit("ExpandedMonV1 must encode all eight exact release profiles")
    if xmon.get("record_bytes")!=64 or xmon.get("legacy_box_record_bytes")!=32:
        raise SystemExit("ExpandedMonV1 size contract changed")
    if xmon["migration_defaults"]["form_id"]!=0 or xmon["migration_defaults"]["ability_id"]!=0:
        raise SystemExit("legacy migration must not infer form or ability")

    print("SILVER all-release ROM/SAV -> GBA Generation-10 import contract: OK")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
