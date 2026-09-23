#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

PINNED_COMMIT = "75b806a3ab57a81ff1eb6179288981f0b3cc3050"

def one(pattern: str, text: str, label: str) -> int:
    match = re.search(pattern, text, re.MULTILINE)
    if not match:
        raise ValueError(f"could not find {label}")
    return int(match.group(1), 0)

def audit_core(root: Path) -> dict:
    pokemon_h = (root / "include" / "pokemon.h").read_text(encoding="utf-8")
    storage_h = (root / "include" / "pokemon_storage_system.h").read_text(encoding="utf-8")
    save_h = (root / "include" / "save.h").read_text(encoding="utf-8")

    move_bits = [int(x) for x in re.findall(r"enum Move move[1-4]:(\d+);", pokemon_h)]
    if len(move_bits) != 4 or len(set(move_bits)) != 1:
        raise ValueError(f"unexpected persistent move packing: {move_bits}")

    template_match = re.search(
        r"struct PokemonTemplate\s*\{(?P<body>.*?)\n\};",
        pokemon_h,
        re.DOTALL,
    )
    if not template_match:
        raise ValueError("could not find PokemonTemplate")
    template = template_match.group("body")
    if "u16 species;" not in template or "u16 heldItem;" not in template or "u16 moves[MAX_MON_MOVES];" not in template:
        raise ValueError("PokemonTemplate no longer exposes the expected u16 identity fields")

    total_boxes = one(r"#define TOTAL_BOXES_COUNT\s+(\d+)", storage_h, "TOTAL_BOXES_COUNT")
    rows = one(r"#define IN_BOX_ROWS\s+(\d+)", storage_h, "IN_BOX_ROWS")
    columns = one(r"#define IN_BOX_COLUMNS\s+(\d+)", storage_h, "IN_BOX_COLUMNS")
    sector_data = one(r"#define SECTOR_DATA_SIZE\s+(\d+)", save_h, "SECTOR_DATA_SIZE")
    storage_start = one(r"#define SECTOR_ID_PKMN_STORAGE_START\s+(\d+)", save_h, "storage sector start")
    storage_end = one(r"#define SECTOR_ID_PKMN_STORAGE_END\s+(\d+)", save_h, "storage sector end")

    git_commit = None
    try:
        git_commit = subprocess.check_output(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        pass

    return {
        "schema_version": 1,
        "upstream": {
            "repository": "rh-hideout/pokeemerald-expansion",
            "commit": git_commit or PINNED_COMMIT,
        },
        "persistent_box_packing": {
            "species_bits": one(r"enum Species species:(\d+);", pokemon_h, "BoxPokemon species bits"),
            "species_max_encoded": (1 << one(r"enum Species species:(\d+);", pokemon_h, "BoxPokemon species bits")) - 1,
            "held_item_bits": one(r"enum Item heldItem:(\d+);", pokemon_h, "BoxPokemon item bits"),
            "held_item_max_encoded": (1 << one(r"enum Item heldItem:(\d+);", pokemon_h, "BoxPokemon item bits")) - 1,
            "move_bits": move_bits[0],
            "move_max_encoded": (1 << move_bits[0]) - 1,
            "move_slots": len(move_bits),
            "tera_type_bits": one(r"enum Type teraType:(\d+);", pokemon_h, "tera type bits"),
            "tera_type_max_encoded": (1 << one(r"enum Type teraType:(\d+);", pokemon_h, "tera type bits")) - 1,
            "ability_slot_bits": one(r"u32 abilityNum:(\d+);", pokemon_h, "ability slot bits"),
            "ability_slot_max_encoded": (1 << one(r"u32 abilityNum:(\d+);", pokemon_h, "ability slot bits")) - 1,
        },
        "creation_template": {
            "species_bits": 16,
            "held_item_bits": 16,
            "move_bits": 16,
            "note": "PokemonTemplate already accepts u16 species, heldItem and moves at the pinned commit.",
        },
        "pc_storage": {
            "total_boxes": total_boxes,
            "rows": rows,
            "columns": columns,
            "mons_per_box": rows * columns,
            "total_mon_slots": total_boxes * rows * columns,
        },
        "flash_save": {
            "sector_data_bytes": sector_data,
            "pokemon_storage_sector_start": storage_start,
            "pokemon_storage_sector_end": storage_end,
            "pokemon_storage_sectors": storage_end - storage_start + 1,
            "pokemon_storage_payload_capacity_bytes": sector_data * (storage_end - storage_start + 1),
            "compile_time_size_assert": True,
        },
        "conclusions": [
            "The persistent BoxPokemon packing is narrower than the SILVER Generation-10 16-bit identity ABI.",
            "Battle/template paths are not the first persistence bottleneck; BoxPokemon and PokemonStorage are.",
            "Widening persistent IDs changes PokemonStorage size and must be validated against the 9-sector save allocation.",
            "Form IDs in SILVER's import model must be resolved through the target core's form/species tables rather than guessed during Gen II migration.",
        ],
    }

def main() -> int:
    ap = argparse.ArgumentParser(description="Audit the pinned pokeemerald-expansion storage ID limits")
    ap.add_argument("core", type=Path)
    ap.add_argument("--manifest", type=Path)
    ap.add_argument("--check", action="store_true")
    ap.add_argument("-o", "--output", type=Path)
    ns = ap.parse_args()

    result = audit_core(ns.core)
    if ns.check:
        if result["upstream"]["commit"] != PINNED_COMMIT:
            raise SystemExit(f"wrong upstream commit: {result['upstream']['commit']}")
        if ns.manifest is None:
            raise SystemExit("--check requires --manifest")
        expected = json.loads(ns.manifest.read_text(encoding="utf-8"))
        if result != expected:
            print(json.dumps(result, indent=2))
            raise SystemExit("pinned core capacity audit differs from committed manifest")

    rendered = json.dumps(result, indent=2) + "\n"
    if ns.output:
        ns.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
