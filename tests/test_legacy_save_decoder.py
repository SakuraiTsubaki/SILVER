from __future__ import annotations

import json
import unittest
from pathlib import Path

from tools.decode_legacy_save import BOX_MON_BYTES, RAW_SRAM_BYTES, checksum16, decode_legacy_save, load_layouts, stored_box_offsets

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = ("jp-rev0","jp-rev1","ko-rev0","en-rev0","de-rev0","fr-rev0","it-rev0","es-rev0")

class LegacySaveDecoderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.layouts = load_layouts(ROOT / "config" / "legacy_save_layouts.json")

    def make_empty_save(self, profile: str) -> bytearray:
        layout = self.layouts[profile]
        data = bytearray(RAW_SRAM_BYTES)
        party = layout["party"]
        data[party["file_offset"]] = 0
        data[party["file_offset"] + 1] = 0xFF
        active = layout["active_box"]
        data[active["file_offset"]] = 0
        data[active["file_offset"] + 1] = 0xFF
        for offset in stored_box_offsets(layout):
            data[offset] = 0
            data[offset + 1] = 0xFF
        cv = layout["check_values"]
        data[cv["first_offset"]] = cv["first_value"]
        data[cv["second_offset"]] = cv["second_value"]
        cs = layout["primary_checksum"]
        value = checksum16(data, cs["start"], cs["end_inclusive"])
        data[cs["stored_offset"]:cs["stored_offset"]+2] = value.to_bytes(2, "little")
        return data

    def test_all_eight_release_profiles_exist(self):
        self.assertEqual(tuple(self.layouts), EXPECTED)

    def test_japanese_geometry(self):
        for profile in ("jp-rev0", "jp-rev1"):
            layout = self.layouts[profile]
            self.assertEqual(layout["party"]["file_offset"], 0x283E)
            self.assertEqual(layout["party"]["bytes"], 0x170)
            self.assertEqual(layout["active_box"]["file_offset"], 0x2D10)
            self.assertEqual(layout["active_box"]["bytes"], 0x548)
            self.assertEqual(layout["stored_boxes"]["box_bytes"], 0x54A)
            self.assertEqual(layout["stored_boxes"]["count"], 9)
            self.assertEqual(layout["stored_boxes"]["mons_per_box"], 30)

    def test_korean_geometry_is_independent(self):
        layout = self.layouts["ko-rev0"]
        self.assertEqual(layout["party"]["file_offset"], 0x28CC)
        self.assertEqual(layout["active_box"]["file_offset"], 0x2DAE)
        self.assertEqual(layout["primary_checksum"]["stored_offset"], 0x2DAB)

    def test_each_western_release_keeps_its_own_profile(self):
        for profile in ("en-rev0","de-rev0","fr-rev0","it-rev0","es-rev0"):
            layout = self.layouts[profile]
            self.assertEqual(layout["party"]["file_offset"], 0x288A)
            self.assertEqual(layout["active_box"]["file_offset"], 0x2D6C)
            self.assertEqual(layout["primary_checksum"]["stored_offset"], 0x2D69)
        self.assertNotIn("western", self.layouts)

    def test_empty_synthetic_save_decodes_for_all_profiles(self):
        for profile in EXPECTED:
            with self.subTest(profile=profile):
                decoded = decode_legacy_save(bytes(self.make_empty_save(profile)), profile=profile, layouts=self.layouts)
                self.assertTrue(decoded["primary_save"]["checksum_valid"])
                self.assertTrue(decoded["primary_save"]["check_value_1_valid"])
                self.assertTrue(decoded["primary_save"]["check_value_2_valid"])
                self.assertEqual(decoded["party"]["count"], 0)
                self.assertTrue(decoded["party"]["terminator_valid"])
                self.assertEqual(decoded["active_box"]["count"], 0)
                self.assertTrue(all(b["terminator_valid"] for b in decoded["stored_boxes"]))

    def test_one_mon_party_normalizes_to_16_bit_identity(self):
        profile = "de-rev0"
        layout = self.layouts[profile]
        data = self.make_empty_save(profile)
        off = layout["party"]["file_offset"]
        data[off] = 1
        data[off+1] = 25
        data[off+2] = 0xFF
        mon_off = off + 8
        raw32 = bytearray(BOX_MON_BYTES)
        raw32[0] = 25
        raw32[1] = 7
        raw32[2:6] = bytes((1,2,3,4))
        raw32[31] = 42
        data[mon_off:mon_off+BOX_MON_BYTES] = raw32
        data[mon_off+BOX_MON_BYTES:mon_off+48] = bytes(range(16))
        cs = layout["primary_checksum"]
        value = checksum16(data, cs["start"], cs["end_inclusive"])
        data[cs["stored_offset"]:cs["stored_offset"]+2] = value.to_bytes(2, "little")
        decoded = decode_legacy_save(bytes(data), profile=profile, layouts=self.layouts)
        mon = decoded["normalized_gba_import"]["party"][0]
        self.assertEqual(mon["species_id"], 25)
        self.assertEqual(mon["item_id"], 7)
        self.assertEqual(mon["move_ids"], [1,2,3,4])
        self.assertEqual(mon["form_id"], 0)
        self.assertEqual(mon["ability_id"], 0)
        self.assertEqual(mon["source_profile"], profile)

    def test_one_mon_stored_box_preserves_exact_release(self):
        profile = "fr-rev0"
        layout = self.layouts[profile]
        data = self.make_empty_save(profile)
        off = stored_box_offsets(layout)[0]
        data[off] = 1
        data[off+1] = 150
        data[off+2] = 0xFF
        mon_off = off + 1 + layout["stored_boxes"]["mons_per_box"] + 1
        raw32 = bytearray(BOX_MON_BYTES)
        raw32[0] = 150
        raw32[1] = 2
        raw32[2:6] = bytes((10,20,30,40))
        raw32[31] = 70
        data[mon_off:mon_off+BOX_MON_BYTES] = raw32
        decoded = decode_legacy_save(bytes(data), profile=profile, layouts=self.layouts)
        mon = decoded["stored_boxes"][0]["mons"][0]
        self.assertTrue(mon["species_matches_list"])
        self.assertEqual(mon["expanded"]["source_profile"], "fr-rev0")

    def test_audited_sample_checksums_are_fixed(self):
        audit = json.loads((ROOT / "analysis" / "save-structure-audit.json").read_text(encoding="utf-8"))
        expected = {"jp-rev0":0x8FD3,"jp-rev1":0x9048,"ko-rev0":0x988D,"en-rev0":0xACF7,"de-rev0":0xAD24,"fr-rev0":0xBA45,"it-rev0":0xAB5E,"es-rev0":0xBA94}
        got = {p["profile_id"]:p["primary_checksum"]["computed"] for p in audit["profiles"]}
        self.assertEqual(got, expected)
        self.assertTrue(all(p["primary_checksum"]["valid"] for p in audit["profiles"]))

if __name__ == "__main__":
    unittest.main()
