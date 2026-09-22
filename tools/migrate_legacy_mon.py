#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import struct
from dataclasses import dataclass
from pathlib import Path

LEGACY_BOXMON_BYTES = 32
LEGACY_TAIL_OFFSET = 6
LEGACY_TAIL_BYTES = 26
EXPANDED_MON_BYTES = 64
MOVE_COUNT = 4

PROFILE_CODES = {
    "jp-rev0": 1,
    "jp-rev1": 2,
    "ko-rev0": 3,
    "en-rev0": 4,
    "de-rev0": 5,
    "fr-rev0": 6,
    "it-rev0": 7,
    "es-rev0": 8,
}
PROFILE_REVISIONS = {
    "jp-rev0": 0, "jp-rev1": 1, "ko-rev0": 0, "en-rev0": 0,
    "de-rev0": 0, "fr-rev0": 0, "it-rev0": 0, "es-rev0": 0,
}
PROFILE_NAMES = {value: key for key, value in PROFILE_CODES.items()}

FLAG_LEGACY_TAIL_VALID = 1 << 0
FLAG_MIGRATED_FROM_GEN2 = 1 << 1
MIGRATION_FLAGS = FLAG_LEGACY_TAIL_VALID | FLAG_MIGRATED_FROM_GEN2

def _u16(value: int, field: str) -> int:
    if not 0 <= value <= 0xFFFF:
        raise ValueError(f"{field} must fit u16")
    return value

def _u8(value: int, field: str) -> int:
    if not 0 <= value <= 0xFF:
        raise ValueError(f"{field} must fit u8")
    return value

@dataclass(frozen=True)
class ExpandedMonV1:
    species_id: int
    form_id: int
    item_id: int
    ability_id: int
    move_ids: tuple[int, int, int, int]
    legacy_tail: bytes
    source_profile: int
    source_revision: int
    feature_flags: int = MIGRATION_FLAGS
    reserved: bytes = bytes(16)

    def __post_init__(self) -> None:
        _u16(self.species_id, "species_id")
        _u16(self.form_id, "form_id")
        _u16(self.item_id, "item_id")
        _u16(self.ability_id, "ability_id")
        if len(self.move_ids) != MOVE_COUNT:
            raise ValueError("move_ids must contain exactly four entries")
        for index, value in enumerate(self.move_ids):
            _u16(value, f"move_ids[{index}]")
        if len(self.legacy_tail) != LEGACY_TAIL_BYTES:
            raise ValueError("legacy_tail must be exactly 26 bytes")
        _u8(self.source_profile, "source_profile")
        _u8(self.source_revision, "source_revision")
        if not 0 <= self.feature_flags <= 0xFFFFFFFF:
            raise ValueError("feature_flags must fit u32")
        if len(self.reserved) != 16:
            raise ValueError("reserved must be exactly 16 bytes")

    @property
    def source_profile_name(self) -> str:
        try:
            return PROFILE_NAMES[self.source_profile]
        except KeyError as exc:
            raise ValueError(f"unknown source profile code {self.source_profile}") from exc

    def serialize(self) -> bytes:
        out = bytearray(EXPANDED_MON_BYTES)
        struct.pack_into("<H", out, 0, self.species_id)
        struct.pack_into("<H", out, 2, self.form_id)
        struct.pack_into("<H", out, 4, self.item_id)
        struct.pack_into("<H", out, 6, self.ability_id)
        for i, move_id in enumerate(self.move_ids):
            struct.pack_into("<H", out, 8 + i * 2, move_id)
        out[16:42] = self.legacy_tail
        out[42] = self.source_profile
        out[43] = self.source_revision
        struct.pack_into("<I", out, 44, self.feature_flags)
        out[48:64] = self.reserved
        return bytes(out)

def migrate_legacy_box_mon(raw: bytes, *, profile: str) -> ExpandedMonV1:
    if len(raw) != LEGACY_BOXMON_BYTES:
        raise ValueError(f"legacy box mon must be exactly {LEGACY_BOXMON_BYTES} bytes")
    try:
        profile_code = PROFILE_CODES[profile]
        revision = PROFILE_REVISIONS[profile]
    except KeyError as exc:
        raise ValueError(f"unknown legacy release profile {profile!r}") from exc
    return ExpandedMonV1(
        species_id=raw[0], form_id=0, item_id=raw[1], ability_id=0,
        move_ids=(raw[2], raw[3], raw[4], raw[5]),
        legacy_tail=raw[LEGACY_TAIL_OFFSET:],
        source_profile=profile_code, source_revision=revision,
    )

def deserialize_expanded_mon(raw: bytes) -> ExpandedMonV1:
    if len(raw) != EXPANDED_MON_BYTES:
        raise ValueError(f"expanded mon must be exactly {EXPANDED_MON_BYTES} bytes")
    return ExpandedMonV1(
        species_id=struct.unpack_from("<H", raw, 0)[0],
        form_id=struct.unpack_from("<H", raw, 2)[0],
        item_id=struct.unpack_from("<H", raw, 4)[0],
        ability_id=struct.unpack_from("<H", raw, 6)[0],
        move_ids=tuple(struct.unpack_from("<H", raw, 8 + i * 2)[0] for i in range(MOVE_COUNT)),
        legacy_tail=raw[16:42], source_profile=raw[42], source_revision=raw[43],
        feature_flags=struct.unpack_from("<I", raw, 44)[0], reserved=raw[48:64],
    )

def downgrade_to_legacy_box_mon(mon: ExpandedMonV1) -> bytes:
    if mon.form_id != 0:
        raise ValueError("legacy Silver cannot represent a nonzero form_id")
    if mon.ability_id != 0:
        raise ValueError("legacy Silver cannot represent a nonzero ability_id")
    ids = [mon.species_id, mon.item_id, *mon.move_ids]
    if any(value > 0xFF for value in ids):
        raise ValueError("legacy Silver identity fields must fit one byte")
    out = bytearray(LEGACY_BOXMON_BYTES)
    out[0] = mon.species_id
    out[1] = mon.item_id
    out[2:6] = bytes(mon.move_ids)
    out[6:] = mon.legacy_tail
    return bytes(out)

def main() -> int:
    ap = argparse.ArgumentParser(description="Migrate one raw Gen II 32-byte box Pokémon record")
    ap.add_argument("input", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("--profile", choices=sorted(PROFILE_CODES), required=True)
    ap.add_argument("--json", action="store_true")
    ns = ap.parse_args()
    mon = migrate_legacy_box_mon(ns.input.read_bytes(), profile=ns.profile)
    ns.output.write_bytes(mon.serialize())
    if ns.json:
        print(json.dumps({
            "species_id":mon.species_id,"form_id":mon.form_id,"item_id":mon.item_id,
            "ability_id":mon.ability_id,"move_ids":list(mon.move_ids),
            "source_profile":mon.source_profile_name,"source_revision":mon.source_revision,
            "record_bytes":EXPANDED_MON_BYTES,
        }, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
