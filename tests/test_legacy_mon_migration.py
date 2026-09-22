from __future__ import annotations

import unittest

from tools.migrate_legacy_mon import (
    EXPANDED_MON_BYTES,
    ExpandedMonV1,
    deserialize_expanded_mon,
    downgrade_to_legacy_box_mon,
    migrate_legacy_box_mon,
)


class LegacyMonMigrationTests(unittest.TestCase):
    def sample(self) -> bytes:
        return bytes(range(32))

    def test_migration_widens_only_identity_fields(self):
        raw = self.sample()
        mon = migrate_legacy_box_mon(raw, profile="jp", revision=1)
        self.assertEqual(mon.species_id, 0)
        self.assertEqual(mon.item_id, 1)
        self.assertEqual(mon.move_ids, (2, 3, 4, 5))
        self.assertEqual(mon.form_id, 0)
        self.assertEqual(mon.ability_id, 0)
        self.assertEqual(mon.legacy_tail, raw[6:])
        self.assertEqual(mon.source_profile_name, "jp")
        self.assertEqual(mon.source_revision, 1)

    def test_serialized_record_is_exactly_64_bytes(self):
        encoded = migrate_legacy_box_mon(self.sample(), profile="western").serialize()
        self.assertEqual(len(encoded), EXPANDED_MON_BYTES)
        self.assertEqual(len(encoded), 64)

    def test_serialization_round_trip_preserves_record(self):
        original = migrate_legacy_box_mon(self.sample(), profile="ko")
        decoded = deserialize_expanded_mon(original.serialize())
        self.assertEqual(decoded, original)

    def test_legacy_round_trip_is_byte_exact_for_all_profiles(self):
        raw = self.sample()
        for profile in ("jp", "ko", "western"):
            with self.subTest(profile=profile):
                mon = migrate_legacy_box_mon(raw, profile=profile)
                self.assertEqual(downgrade_to_legacy_box_mon(mon), raw)

    def test_extended_species_is_not_downgradable(self):
        mon = migrate_legacy_box_mon(self.sample(), profile="jp")
        expanded = ExpandedMonV1(
            species_id=1025,
            form_id=mon.form_id,
            item_id=mon.item_id,
            ability_id=mon.ability_id,
            move_ids=mon.move_ids,
            legacy_tail=mon.legacy_tail,
            source_profile=mon.source_profile,
            source_revision=mon.source_revision,
        )
        with self.assertRaises(ValueError):
            downgrade_to_legacy_box_mon(expanded)

    def test_form_and_ability_are_never_inferred(self):
        mon = migrate_legacy_box_mon(bytes([251, 7, 1, 2, 3, 4]) + bytes(26), profile="western")
        self.assertEqual(mon.form_id, 0)
        self.assertEqual(mon.ability_id, 0)

    def test_nonzero_modern_fields_block_legacy_downgrade(self):
        base = migrate_legacy_box_mon(self.sample(), profile="ko")
        for field in ("form_id", "ability_id"):
            kwargs = dict(base.__dict__)
            kwargs[field] = 1
            with self.subTest(field=field), self.assertRaises(ValueError):
                downgrade_to_legacy_box_mon(ExpandedMonV1(**kwargs))


if __name__ == "__main__":
    unittest.main()
