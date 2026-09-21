#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "expansion.json"

REQUIRED_16 = {"species", "form", "move", "item", "ability"}
REQUIRED = {
    "target_generation": 10,
    "forward_compatible": True,
}


def main() -> int:
    data = json.loads(CONFIG.read_text(encoding="utf-8"))

    for key, value in REQUIRED.items():
        if data.get(key) != value:
            raise SystemExit(f"{key} must be {value!r}")

    widths = data["id_widths"]
    for key in REQUIRED_16:
        if widths.get(key, 0) < 16:
            raise SystemExit(f"{key} ID must be at least 16-bit")

    if widths.get("string", 0) < 32:
        raise SystemExit("string ID must be at least 32-bit")

    far = data["far_pointer"]
    if far.get("logical_bank_bits", 0) < 16 or far.get("offset_bits", 0) < 16:
        raise SystemExit("far pointer must preserve 16-bit logical bank and offset")
    if far.get("serialized_bytes") != 4:
        raise SystemExit("far pointer ABI must serialize to four bytes")

    save = data["save"]
    if not save.get("species_and_form_are_separate"):
        raise SystemExit("save ABI must store species and form separately")
    if not save.get("migration_required"):
        raise SystemExit("legacy save migration must be explicit")

    rom = data["rom"]
    if not rom.get("require_rtc_preservation"):
        raise SystemExit("Silver expansion must preserve an RTC-capable design path")
    if not rom.get("require_mapper_abstraction"):
        raise SystemExit("mapper abstraction is required before bulk content import")

    print("SILVER expansion contract: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
