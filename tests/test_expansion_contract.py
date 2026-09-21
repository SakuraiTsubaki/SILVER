from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

class ExpansionContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg=json.loads((ROOT/"config"/"expansion.json").read_text(encoding="utf-8"))
        cls.baseline=json.loads((ROOT/"analysis"/"rom-save-baseline.json").read_text(encoding="utf-8"))
        cls.profiles=json.loads((ROOT/"config"/"legacy_save_profiles.json").read_text(encoding="utf-8"))["profiles"]

    def test_observed_rom_hardware(self):
        self.assertEqual(len(self.baseline["roms"]),8)
        self.assertTrue(all(r["cartridge_type"]==0x10 for r in self.baseline["roms"]))
        self.assertTrue(all(r["ram_size_code"]==0x03 for r in self.baseline["roms"]))

    def test_observed_rom_sizes(self):
        jp={r["size"] for r in self.baseline["roms"] if r["title"]=="POKEMON_SLVAAXJ"}
        other={r["size"] for r in self.baseline["roms"] if r["title"]!="POKEMON_SLVAAXJ"}
        self.assertEqual(jp,{1048576})
        self.assertEqual(other,{2097152})

    def test_observed_save_wrapper(self):
        self.assertEqual(len(self.baseline["saves"]),8)
        self.assertTrue(all(s["raw_sram_bytes"]==32768 for s in self.baseline["saves"]))
        self.assertTrue(all(s["host_tail_bytes"]==44 for s in self.baseline["saves"]))

    def test_legacy_profiles_are_distinct(self):
        self.assertEqual((self.profiles["jp"]["boxes"],self.profiles["jp"]["mons_per_box"]),(9,30))
        self.assertEqual((self.profiles["ko"]["boxes"],self.profiles["ko"]["mons_per_box"]),(14,20))
        self.assertEqual((self.profiles["western"]["boxes"],self.profiles["western"]["mons_per_box"]),(14,20))
        self.assertEqual(self.profiles["jp"]["hall_of_fame_teams"],50)
        self.assertEqual(self.profiles["western"]["hall_of_fame_teams"],30)

    def test_widened_identity_boundary(self):
        for key in ("species","form","move","item","ability"):
            self.assertGreaterEqual(self.cfg["id_widths"][key],16)

    def test_rtc_mapper_boundary(self):
        rom=self.cfg["rom"]
        self.assertEqual(rom["legacy_cartridge_type"],0x10)
        self.assertEqual(rom["native_mbc3_rom_bank_ceiling"],128)
        self.assertTrue(rom["require_rtc_preservation"])
        self.assertTrue(rom["require_mapper_abstraction"])

    def test_legacy_import_is_not_in_place(self):
        save=self.cfg["save"]
        self.assertTrue(save["migration_required"])
        self.assertTrue(save["legacy_import_is_read_only"])
        self.assertEqual(save["legacy_profiles"],["jp","ko","western"])

if __name__=="__main__":
    unittest.main()
