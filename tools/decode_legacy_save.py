#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from tools.migrate_legacy_mon import migrate_legacy_box_mon

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LAYOUTS = ROOT / "config" / "legacy_save_layouts.json"
RAW_SRAM_BYTES = 32768
BOX_MON_BYTES = 32
PARTY_MON_BYTES = 48

def load_layouts(path: Path = DEFAULT_LAYOUTS) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    profiles = data.get("profiles", {})
    if not profiles:
        raise ValueError("legacy save layout config contains no profiles")
    return profiles

def checksum16(data: bytes, start: int, end_inclusive: int) -> int:
    if not (0 <= start <= end_inclusive < len(data)):
        raise ValueError("checksum range is outside SRAM")
    return sum(data[start:end_inclusive + 1]) & 0xFFFF

def _slice(data: bytes, offset: int, size: int, label: str) -> bytes:
    end = offset + size
    if offset < 0 or end > len(data):
        raise ValueError(f"{label} extends outside SRAM: 0x{offset:x}..0x{end:x}")
    return data[offset:end]

def _expanded_mon_json(raw32: bytes, profile: str) -> dict[str, Any]:
    mon = migrate_legacy_box_mon(raw32, profile=profile)
    return {
        "species_id": mon.species_id,
        "form_id": mon.form_id,
        "item_id": mon.item_id,
        "ability_id": mon.ability_id,
        "move_ids": list(mon.move_ids),
        "source_profile": mon.source_profile_name,
        "source_revision": mon.source_revision,
        "legacy_tail_hex": mon.legacy_tail.hex(),
        "expanded_record_hex": mon.serialize().hex(),
    }

def decode_box_mon(raw32: bytes, profile: str, *, party_tail: bytes | None = None) -> dict[str, Any]:
    if len(raw32) != BOX_MON_BYTES:
        raise ValueError("box Pokémon record must be exactly 32 bytes")
    out = {
        "legacy": {
            "species": raw32[0],
            "item": raw32[1],
            "moves": list(raw32[2:6]),
            "ot_id_le": int.from_bytes(raw32[6:8], "little"),
            "exp_be24": int.from_bytes(raw32[8:11], "big"),
            "stat_exp_le": [int.from_bytes(raw32[11+i*2:13+i*2], "little") for i in range(5)],
            "dvs_le": int.from_bytes(raw32[21:23], "little"),
            "pp": list(raw32[23:27]),
            "happiness": raw32[27],
            "pokerus": raw32[28],
            "unused": list(raw32[29:31]),
            "level": raw32[31],
            "raw_hex": raw32.hex(),
        },
        "expanded": _expanded_mon_json(raw32, profile),
    }
    if party_tail is not None:
        if len(party_tail) != 16:
            raise ValueError("party-only tail must be exactly 16 bytes")
        out["party"] = {
            "status": party_tail[0],
            "unused": party_tail[1],
            "hp_le": int.from_bytes(party_tail[2:4], "little"),
            "max_hp_le": int.from_bytes(party_tail[4:6], "little"),
            "stats_le": [int.from_bytes(party_tail[6+i*2:8+i*2], "little") for i in range(5)],
            "raw_hex": party_tail.hex(),
        }
    return out

def _terminator_valid(species: list[int], count: int) -> bool:
    return 0 <= count < len(species) and species[count] == 0xFF

def decode_party(sram: bytes, profile: str, layout: dict[str, Any]) -> dict[str, Any]:
    cfg = layout["party"]
    raw = _slice(sram, cfg["file_offset"], cfg["bytes"], "party")
    capacity = cfg["capacity"]
    count = raw[0]
    if count > capacity:
        raise ValueError(f"party count {count} exceeds capacity {capacity}")
    species = list(raw[1:1+capacity+1])
    mons_offset = 1 + capacity + 1
    ot_offset = mons_offset + capacity * PARTY_MON_BYTES
    nick_offset = ot_offset + capacity * cfg["ot_name_bytes"]
    expected = nick_offset + capacity * cfg["nickname_bytes"]
    if expected != len(raw):
        raise ValueError(f"party geometry mismatch: expected {expected}, got {len(raw)}")
    mons = []
    for i in range(count):
        rec = raw[mons_offset+i*PARTY_MON_BYTES:mons_offset+(i+1)*PARTY_MON_BYTES]
        mon = decode_box_mon(rec[:BOX_MON_BYTES], profile, party_tail=rec[BOX_MON_BYTES:])
        mon["slot"] = i
        mon["list_species"] = species[i]
        mon["species_matches_list"] = species[i] == rec[0]
        mon["ot_name_raw_hex"] = raw[ot_offset+i*cfg["ot_name_bytes"]:ot_offset+(i+1)*cfg["ot_name_bytes"]].hex()
        mon["nickname_raw_hex"] = raw[nick_offset+i*cfg["nickname_bytes"]:nick_offset+(i+1)*cfg["nickname_bytes"]].hex()
        mons.append(mon)
    return {
        "file_offset": cfg["file_offset"], "bytes": cfg["bytes"], "count": count,
        "capacity": capacity, "species_list": species,
        "terminator_valid": _terminator_valid(species, count),
        "mons": mons, "raw_sha256": hashlib.sha256(raw).hexdigest(),
    }

def decode_box(raw: bytes, profile: str, layout: dict[str, Any], *, box_index: int, file_offset: int, active: bool) -> dict[str, Any]:
    cfg = layout["stored_boxes"]
    capacity = cfg["mons_per_box"]
    count = raw[0]
    if count > capacity:
        raise ValueError(f"box {box_index} count {count} exceeds capacity {capacity}")
    species = list(raw[1:1+capacity+1])
    mons_offset = 1 + capacity + 1
    ot_offset = mons_offset + capacity * BOX_MON_BYTES
    nick_offset = ot_offset + capacity * cfg["ot_name_bytes"]
    payload_end = nick_offset + capacity * cfg["nickname_bytes"]
    expected = payload_end if active else payload_end + 2
    if expected != len(raw):
        raise ValueError(f"box {box_index} geometry mismatch: expected {expected}, got {len(raw)}")
    mons = []
    for i in range(count):
        rec = raw[mons_offset+i*BOX_MON_BYTES:mons_offset+(i+1)*BOX_MON_BYTES]
        mon = decode_box_mon(rec, profile)
        mon["slot"] = i
        mon["list_species"] = species[i]
        mon["species_matches_list"] = species[i] == rec[0]
        mon["ot_name_raw_hex"] = raw[ot_offset+i*cfg["ot_name_bytes"]:ot_offset+(i+1)*cfg["ot_name_bytes"]].hex()
        mon["nickname_raw_hex"] = raw[nick_offset+i*cfg["nickname_bytes"]:nick_offset+(i+1)*cfg["nickname_bytes"]].hex()
        mons.append(mon)
    out = {
        "box_index": box_index, "active": active, "file_offset": file_offset,
        "bytes": len(raw), "count": count, "capacity": capacity,
        "species_list": species, "terminator_valid": _terminator_valid(species, count),
        "mons": mons, "raw_sha256": hashlib.sha256(raw).hexdigest(),
    }
    if not active:
        out["padding_hex"] = raw[payload_end:].hex()
    return out

def stored_box_offsets(layout: dict[str, Any]) -> list[int]:
    cfg = layout["stored_boxes"]
    offsets = []
    for group in cfg["groups"]:
        offsets.extend(group["file_offset"] + i * cfg["box_bytes"] for i in range(group["count"]))
    if len(offsets) != cfg["count"]:
        raise ValueError(f"stored box groups describe {len(offsets)} boxes, expected {cfg['count']}")
    return offsets

def decode_legacy_save(data: bytes, *, profile: str, layouts: dict[str, Any] | None = None) -> dict[str, Any]:
    layouts = layouts or load_layouts()
    try:
        layout = layouts[profile]
    except KeyError as exc:
        raise ValueError(f"unknown Silver release profile {profile!r}") from exc
    if len(data) < RAW_SRAM_BYTES:
        raise ValueError("save is smaller than the 32 KiB Silver SRAM image")
    sram = data[:RAW_SRAM_BYTES]
    host_tail = data[RAW_SRAM_BYTES:]
    cs = layout["primary_checksum"]
    computed = checksum16(sram, cs["start"], cs["end_inclusive"])
    stored = int.from_bytes(_slice(sram, cs["stored_offset"], 2, "primary checksum"), "little")
    cv = layout["check_values"]
    party = decode_party(sram, profile, layout)
    active_cfg = layout["active_box"]
    active_box = decode_box(
        _slice(sram, active_cfg["file_offset"], active_cfg["bytes"], "active box"),
        profile, layout, box_index=0, file_offset=active_cfg["file_offset"], active=True,
    )
    stored_boxes = []
    for i, offset in enumerate(stored_box_offsets(layout), start=1):
        stored_boxes.append(decode_box(
            _slice(sram, offset, layout["stored_boxes"]["box_bytes"], f"stored box {i}"),
            profile, layout, box_index=i, file_offset=offset, active=False,
        ))
    return {
        "schema_version": 1, "source_profile": profile,
        "layout_family": layout["layout_family"], "language": layout["language"],
        "save_bytes": len(data), "raw_sram_bytes": RAW_SRAM_BYTES,
        "raw_sram_sha256": hashlib.sha256(sram).hexdigest(),
        "host_tail_bytes": len(host_tail),
        "host_tail_sha256": hashlib.sha256(host_tail).hexdigest() if host_tail else None,
        "primary_save": {
            "checksum_start": cs["start"], "checksum_end_inclusive": cs["end_inclusive"],
            "checksum_offset": cs["stored_offset"], "checksum_computed": computed,
            "checksum_stored": stored, "checksum_valid": computed == stored,
            "check_value_1": sram[cv["first_offset"]],
            "check_value_1_valid": sram[cv["first_offset"]] == cv["first_value"],
            "check_value_2": sram[cv["second_offset"]],
            "check_value_2_valid": sram[cv["second_offset"]] == cv["second_value"],
        },
        "party": party, "active_box": active_box, "stored_boxes": stored_boxes,
        "normalized_gba_import": {
            "source_profile": profile,
            "party": [m["expanded"] for m in party["mons"]],
            "boxes": [[m["expanded"] for m in b["mons"]] for b in stored_boxes],
            "active_box": [m["expanded"] for m in active_box["mons"]],
        },
    }

def main() -> int:
    ap = argparse.ArgumentParser(description="Decode an audited Pokémon Silver legacy SAV")
    ap.add_argument("save", type=Path)
    ap.add_argument("--profile", required=True)
    ap.add_argument("--layouts", type=Path, default=DEFAULT_LAYOUTS)
    ap.add_argument("-o", "--output", type=Path)
    ap.add_argument("--normalized-only", action="store_true")
    ns = ap.parse_args()
    decoded = decode_legacy_save(ns.save.read_bytes(), profile=ns.profile, layouts=load_layouts(ns.layouts))
    payload = decoded["normalized_gba_import"] if ns.normalized_only else decoded
    rendered = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if ns.output:
        ns.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
