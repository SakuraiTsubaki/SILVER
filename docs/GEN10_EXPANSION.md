# Generation 10 expansion foundation

SILVER's expansion rules are derived from the inspected Generation II ROM and save formats, not from a blank modern schema.

Read `ROM_SAVE_EXPANSION_BASELINE.md` first.

## What the original format forces us to change

The retail Pokémon structures store species, held item and each move as one-byte values. That makes widening those identities a real serialization/runtime migration boundary.

The inspected cartridges all use MBC3 + timer + RAM + battery and 32 KiB SRAM. Localized Silver already reaches 2 MiB / 128 ROM banks, so a larger content build cannot obtain more native MBC3 ROM banks by changing a constant.

The legacy save layout also varies by release family: Japanese is 9×30 boxes while Korean/Western is 14×20, with different backup placement and string footprints.

## Extended ABI

| Domain | Width | Rule |
| --- | ---: | --- |
| Species ID | 16-bit | Species and form remain separate |
| Form ID | 16-bit | Independent identity field |
| Move ID | 16-bit | Converted from legacy byte values |
| Item ID | 16-bit | Converted from legacy byte values |
| Ability ID | 16-bit | New native engine field |
| Type ID | 8-bit | Can be revised later without touching mon identity |
| Generation ID | 8-bit | Ruleset/provenance selector |
| String ID | 32-bit | Decoupled from ROM-local text offsets |
| Feature flags | 32-bit | Explicit mechanics gates |
| Far pointer | 16-bit logical bank + 16-bit offset | Physical mapper translation is separate |

## Compatibility boundary

Legacy save import is read-only and profile-driven:

- `jp`
- `ko`
- `western`

The imported record is normalized into an internal model and only then written to the new expanded save format.

Bytes after the first 32 KiB of the supplied save files are treated as host-side metadata, not cartridge SRAM.

## ROM banking boundary

The engine may use logical bank IDs wider than MBC3, but a backend must translate those IDs to a physical or virtual storage mechanism while keeping RTC behavior intact.

The final expanded mapper/backend is deliberately still undecided. Choosing it requires implementation/testing against the original RTC/save behavior, not just capacity estimates.

## Next code work

1. import the Silver source baseline into this repository;
2. implement ROM identity and legacy-save profile detection;
3. implement JP/KO/Western SRAM decoders;
4. define the profile-independent expanded Pokémon/save structures;
5. replace one-byte identity assumptions at runtime boundaries;
6. implement and test the RTC-preserving expanded banking backend.
