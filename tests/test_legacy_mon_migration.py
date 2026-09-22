from __future__ import annotations
import unittest
from tools.migrate_legacy_mon import (
    EXPANDED_MON_BYTES, PROFILE_CODES, ExpandedMonV1,
    deserialize_expanded_mon, downgrade_to_legacy_box_mon, migrate_legacy_box_mon,
)

class LegacyMonMigrationTests(unittest.TestCase):
    PROFILES=("jp-rev0","jp-rev1","ko-rev0","en-rev0","de-rev0","fr-rev0","it-rev0","es-rev0")

    def sample(self)->bytes:
        return bytes(range(32))

    def test_all_eight_profiles_have_unique_codes(self):
        self.assertEqual(set(PROFILE_CODES),set(self.PROFILES))
        self.assertEqual(len(set(PROFILE_CODES.values())),8)

    def test_migration_widens_only_identity_fields(self):
        raw=self.sample()
        mon=migrate_legacy_box_mon(raw,profile="jp-rev1")
        self.assertEqual(mon.species_id,0)
        self.assertEqual(mon.item_id,1)
        self.assertEqual(mon.move_ids,(2,3,4,5))
        self.assertEqual(mon.form_id,0)
        self.assertEqual(mon.ability_id,0)
        self.assertEqual(mon.legacy_tail,raw[6:])
        self.assertEqual(mon.source_profile_name,"jp-rev1")
        self.assertEqual(mon.source_revision,1)

    def test_every_release_profile_round_trips_byte_exactly(self):
        raw=self.sample()
        for profile in self.PROFILES:
            with self.subTest(profile=profile):
                mon=migrate_legacy_box_mon(raw,profile=profile)
                self.assertEqual(len(mon.serialize()),EXPANDED_MON_BYTES)
                self.assertEqual(downgrade_to_legacy_box_mon(mon),raw)
                self.assertEqual(deserialize_expanded_mon(mon.serialize()),mon)

    def test_form_and_ability_are_never_inferred(self):
        for profile in self.PROFILES:
            with self.subTest(profile=profile):
                mon=migrate_legacy_box_mon(bytes([251,7,1,2,3,4])+bytes(26),profile=profile)
                self.assertEqual(mon.form_id,0)
                self.assertEqual(mon.ability_id,0)

    def test_extended_species_is_not_downgradable(self):
        mon=migrate_legacy_box_mon(self.sample(),profile="en-rev0")
        kwargs=dict(mon.__dict__)
        kwargs["species_id"]=1025
        with self.assertRaises(ValueError):
            downgrade_to_legacy_box_mon(ExpandedMonV1(**kwargs))

if __name__=="__main__":
    unittest.main()
