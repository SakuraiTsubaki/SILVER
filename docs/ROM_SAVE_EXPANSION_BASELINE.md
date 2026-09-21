# ROM + save baseline for SILVER expansion

This expansion baseline was derived from the user-supplied Silver ROM and save pairs before changing the engine format.

## Observed ROM hardware contract

All eight inspected retail ROMs use cartridge type `0x10`: **MBC3 + timer + RAM + battery**.

All eight declare 32 KiB cartridge RAM (`RAM size code 0x03`), which is four 8 KiB SRAM banks.

The Japanese Rev.0 and Rev.1 ROMs are 1 MiB (64 ROM banks). The Korean and five Western localized ROMs are 2 MiB (128 ROM banks), which reaches the normal MBC3 ROM-bank ceiling used by these releases.

The expansion layer therefore cannot treat RTC support as optional and cannot assume that adding more ROM banks is a normal MBC3 operation.

## Observed save files

Every supplied `.sav` is 32,812 bytes:

- first 32,768 bytes: the complete four-bank cartridge SRAM image;
- final 44 bytes: host-side data outside the cartridge's declared SRAM capacity.

The engine importer must treat the first 32 KiB as the raw legacy SRAM image. The extra 44 bytes must not be silently folded into the in-game save address space.

The supplied Japanese Rev.0 and Rev.1 saves have the same physical SRAM size. Their observed 32 KiB cores differ by 52 bytes in this particular state. This is useful evidence that revision does not imply a different physical SRAM size, but it is not a claim that arbitrary saves are byte-identical.

## Source-confirmed legacy layouts

The binary evidence was cross-checked against the current Japanese, Korean, and Western Gold/Silver disassembly layouts.

### Japanese

- 9 PC boxes
- 30 Pokémon per box
- total PC capacity 270
- 50 Hall of Fame teams
- boxes 1-6 in SRAM bank 2
- boxes 7-9 in SRAM bank 3
- backup save in SRAM bank 3 at `0xB200`
- active box in SRAM bank 1 at `0xAD10`

### Korean

- 14 PC boxes
- 20 Pokémon per box
- total PC capacity 280
- 30 Hall of Fame teams
- boxes 1-7 in SRAM bank 2
- boxes 8-14 in SRAM bank 3
- backup save split across SRAM banks
- Hangul mail storage changes string footprint

### Western localized releases

- 14 PC boxes
- 20 Pokémon per box
- total PC capacity 280
- 30 Hall of Fame teams
- boxes 1-7 in SRAM bank 2
- boxes 8-14 in SRAM bank 3
- backup save split across SRAM banks

## Expansion consequences

SILVER must have **three legacy import profiles**: Japanese, Korean, and Western. A single hard-coded Generation II save layout is incorrect.

The new save format must be independent from those profiles. Legacy data is decoded into an internal representation and then serialized into the expanded format. Raw legacy SRAM must remain importable and must never be rewritten in place as if all regions shared one layout.

The ROM expansion path must preserve an RTC-capable compatibility layer. Since the localized retail ROMs already occupy 128 16-KiB ROM banks, content growth beyond 2 MiB requires a new physical/virtual banking backend rather than pretending MBC3 has more native banks.

Original Pokémon structures also confirm the principal ID bottlenecks: species, held item, and each move are one byte in box/party data. Widening those identities is therefore an actual migration boundary, not just a future-proofing preference.

## Next implementation boundary

Before importing bulk data, implement:

1. ROM identity/profile detection;
2. read-only legacy SRAM decoders for JP / KO / Western;
3. a profile-independent expanded save model;
4. mapper/RTC abstraction that can translate logical banks without changing content-table IDs;
5. widened Pokémon runtime structures and explicit legacy conversion routines.
