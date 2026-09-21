# SILVER

Modernized **Pokémon Silver / Pocket Monsters Gin** project.

The first implementation priority is a **Generation-10-ready engine foundation** before importing bulk game content.

## Expansion foundation

- 16-bit species IDs
- 16-bit form IDs, stored separately from species
- 16-bit move IDs
- 16-bit item IDs
- 16-bit ability IDs
- 32-bit string IDs
- 32-bit feature/mechanics flags
- mapper-independent 4-byte far pointers
- versioned save format with explicit legacy migration
- RTC preservation required by the mapper abstraction

The expansion ABI is defined in `config/expansion.json` and
`engine/abi/extended_ids.inc`.

See `docs/GEN10_EXPANSION.md` for the design rules.

## Validation

```sh
python tools/validate_expansion.py
python -m unittest discover -s tests -v
```

Generation 10 readiness means the engine can accept later official data without
another global ID/save/addressing format break. It does not predefine unreleased
content.
