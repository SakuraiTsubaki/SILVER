#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

ANCHOR = """    u16 shinyModifier:1;
    u16 unused_1E:1;

    union
"""
REPLACEMENT = """    u16 shinyModifier:1;
    u16 unused_1E:1;

    // SILVER Generation-10 capacity probe only.
    // One 32-bit sidecar can hold the high bits for:
    // species (5) + held item (6) + four moves (5 * 4) = 31 bits.
    u32 silverIdExtensionProbe;

    union
"""

def apply_probe(root: Path) -> None:
    path = root / "include" / "pokemon.h"
    text = path.read_text(encoding="utf-8")
    if "silverIdExtensionProbe" in text:
        return
    if ANCHOR not in text:
        raise SystemExit("pinned BoxPokemon anchor not found; refuse to guess a patch location")
    path.write_text(text.replace(ANCHOR, REPLACEMENT, 1), encoding="utf-8")

def main() -> int:
    ap = argparse.ArgumentParser(description="Probe whether +4 bytes per BoxPokemon still fits the pinned save layout")
    ap.add_argument("core", type=Path)
    ns = ap.parse_args()
    apply_probe(ns.core)
    print("Applied SILVER +32-bit BoxPokemon capacity probe")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
