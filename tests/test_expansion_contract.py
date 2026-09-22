from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
EXPECTED=("jp-rev0","jp-rev1","ko-rev0","en-rev0","de-rev0","fr-rev0","it-rev0","es-rev0")

class ExpansionContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg=json.loads((ROOT/"config"/"expansion.json").read_text(encoding="utf-8"))
        cls.baseline=json.loads((ROOT/"analysis"/"rom-save-baseline.json").read_text(encoding="utf-8"))
        cls.profiles=json.loads((ROOT/"config"/"legacy_save_profiles.json").read_text(encoding="utf-8"))["profiles"]

    def test_all_eight_observed_roms_preserved(self):
        releases=self.baseline["releases"]
        self.assertEqual(len(releases),8)
        self.assertEqual(tuple(r["profile_id"] for r in releases),EXPECTED)
        self.assertTrue(all(r["rom"]["cartridge_type"]==0x10 for r in releases))
        self.assertTrue(all(r["rom"]["ram_size_code"]==0x03 for r in releases))
        self.assertTrue(all(r["rom"]["header_checksum_valid"] for r in releases))
        self.assertTrue(all(r["rom"]["global_checksum_valid"] for r in releases))

    def test_observed_rom_sizes(self):
        by_profile={r["profile_id"]:r["rom"]["bytes"] for r in self.baseline["releases"]}
        self.assertEqual(by_profile["jp-rev0"],1048576)
        self.assertEqual(by_profile["jp-rev1"],1048576)
        for profile in EXPECTED[2:]:
            self.assertEqual(by_profile[profile],2097152)

    def test_all_eight_save_wrappers_preserved(self):
        releases=self.baseline["releases"]
        self.assertTrue(all(r["save"]["raw_sram_bytes"]==32768 for r in releases))
        self.assertTrue(all(r["save"]["host_tail_bytes"]==44 for r in releases))
        self.assertTrue(all(len(r["save"]["sram_bank_sha256"])==4 for r in releases))

    def test_release_profiles_are_not_collapsed(self):
        self.assertEqual(tuple(self.profiles),EXPECTED)
        self.assertNotIn("jp",self.profiles)
        self.assertNotIn("ko",self.profiles)
        self.assertNotIn("western",self.profiles)
        self.assertEqual((self.profiles["jp-rev0"]["boxes"],self.profiles["jp-rev0"]["mons_per_box"]),(9,30))
        self.assertEqual((self.profiles["jp-rev1"]["boxes"],self.profiles["jp-rev1"]["mons_per_box"]),(9,30))
        for profile in EXPECTED[2:]:
            self.assertEqual((self.profiles[profile]["boxes"],self.profiles[profile]["mons_per_box"]),(14,20))

    def test_widened_identity_boundary(self):
        for key in ("species","form","move","item","ability"):
            self.assertGreaterEqual(self.cfg["id_widths"][key],16)

    def test_gba_runtime_keeps_gbc_as_import_evidence(self):
        self.assertEqual(self.cfg["runtime"]["platform"],"Game Boy Advance")
        self.assertFalse(self.cfg["runtime"]["legacy_gbc_runtime"])
        legacy=self.cfg["legacy_rom"]
        self.assertEqual(legacy["cartridge_type"],0x10)
        self.assertEqual(legacy["native_mbc3_rom_bank_ceiling"],128)
        self.assertEqual(legacy["runtime_role"],"reference-and-import-only")
        self.assertTrue(legacy["preserve_rtc_semantics_in_remake"])

    def test_legacy_import_is_release_specific_and_read_only(self):
        save=self.cfg["save"]
        self.assertTrue(save["migration_required"])
        self.assertTrue(save["legacy_import_is_read_only"])
        self.assertTrue(save["release_identity_preserved"])
        self.assertEqual(tuple(save["legacy_profiles"]),EXPECTED)
        self.assertEqual(save["legacy_profile_count"],8)

if __name__=="__main__":
    unittest.main()
