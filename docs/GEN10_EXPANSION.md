# Generation 10 expansion foundation

SILVER must not inherit Generation II's one-byte identity assumptions as permanent engine ABI.

This foundation is intentionally content-agnostic. It does **not** invent Generation 10 species, moves, items, abilities, types, forms, or mechanics. It reserves enough identity space and versioning so those datasets can be added later without another global format break.

## ABI decisions

| Domain | Width | Rule |
| --- | ---: | --- |
| Species ID | 16-bit | Species and form are never packed together |
| Form ID | 16-bit | Independent from species |
| Move ID | 16-bit | No 8-bit table index ABI |
| Item ID | 16-bit | No 8-bit table index ABI |
| Ability ID | 16-bit | Native field, not an afterthought |
| Type ID | 8-bit | 0 and 0xFF reserved |
| Generation ID | 8-bit | Data provenance / ruleset selection |
| String ID | 32-bit | Text assets may outgrow bank-local indexes |
| Feature flags | 32-bit | Mechanics are gated explicitly |
| Far pointer | 16-bit logical bank + 16-bit offset | Physical mapper translation is separate |

ID 0 is reserved for NONE. The all-ones value for each width is reserved as INVALID, so valid data must never consume the sentinel.

## Why logical banks come first

Original Silver is tied to Game Boy cartridge banking and RTC behavior. A future large-content build may need a different physical mapper or a virtualized data backend, but choosing that now would couple every table to a hardware decision.

All new cross-bank data references therefore use a logical 4-byte far pointer:

```text
u16 logical_bank
u16 offset
```

The mapper layer will translate logical banks to the physical backend. This preserves the option to keep an RTC-capable legacy path while also allowing a larger expanded build.

## Save contract

The expanded save format must begin with a versioned header and feature flags. Species and form are stored separately. Migration from an original Generation II save is an explicit conversion step rather than silent reinterpretation of bytes.

A future save implementation must provide:

- `u16 format_version`
- `u32 feature_flags`
- independent `u16 species_id`
- independent `u16 form_id`
- explicit migration code for legacy records
- checksummed/versioned sections so new fields can be added without shifting every old record

## Content tables

Do not key extended tables by raw ROM address. Key them by stable IDs and resolve them through table descriptors/far pointers.

The first engine import must replace one-byte assumptions at boundaries before bulk content is added:

1. species/form lookup
2. moves
3. items
4. abilities
5. type/ruleset data
6. text/string lookup
7. sprite/graphics lookup
8. save serialization
9. link/battle serialization
10. scripting/event parameters

## Compatibility rule

Legacy behavior can have adapters, but new code must not expose an 8-bit species/move/item identity as a public engine interface.

The target is Generation 10 readiness, not Generation 10 guesswork.
