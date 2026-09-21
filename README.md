# SILVER

Modernized **Pokémon Silver / Pocket Monsters Gin** project.

Expansion work is driven by the actual Silver ROM and save formats first, then widened for later-generation content.

## Verified baseline used by this repository

The inspected retail ROM set contains Japanese Rev.0/Rev.1, Korean, English, German, French, Italian and Spanish Silver.

Observed hardware facts:

- cartridge type `0x10`: MBC3 + timer + RAM + battery
- 32 KiB SRAM on every inspected ROM
- Japanese ROMs: 1 MiB
- Korean/Western localized ROMs: 2 MiB
- supplied save files: 32 KiB raw SRAM + 44 bytes of host-side trailing data

The legacy save layouts are **not one format**:

- Japanese: 9 boxes × 30 Pokémon, 50 Hall of Fame teams
- Korean: 14 boxes × 20 Pokémon, 30 Hall of Fame teams
- Western: 14 boxes × 20 Pokémon, 30 Hall of Fame teams

See `analysis/rom-save-baseline.json`,
`config/legacy_save_profiles.json`, and
`docs/ROM_SAVE_EXPANSION_BASELINE.md`.

## Expansion direction

The new engine ABI widens species/form/move/item/ability identities to 16-bit,
but legacy SRAM is imported through region-specific read-only decoders rather
than rewritten in place.

ROM growth beyond the observed 128-bank localized releases must go through an
RTC-preserving mapper abstraction; it must not pretend native MBC3 has extra
banks.

## Validation

```sh
python tools/validate_expansion.py
python -m unittest discover -s tests -v
```

No ROM binaries are stored in this repository.
