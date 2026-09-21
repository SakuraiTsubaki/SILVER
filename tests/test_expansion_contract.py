from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ExpansionContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg = json.loads((ROOT / "config" / "expansion.json").read_text(encoding="utf-8"))

    def test_generation_10_target(self):
        self.assertEqual(self.cfg["target_generation"], 10)
        self.assertTrue(self.cfg["forward_compatible"])

    def test_core_ids_are_not_8_bit(self):
        widths = self.cfg["id_widths"]
        for key in ("species", "form", "move", "item", "ability"):
            self.assertGreaterEqual(widths[key], 16, key)

    def test_species_and_form_are_separate(self):
        self.assertTrue(self.cfg["save"]["species_and_form_are_separate"])

    def test_far_pointer_is_mapper_independent(self):
        far = self.cfg["far_pointer"]
        self.assertGreaterEqual(far["logical_bank_bits"], 16)
        self.assertGreaterEqual(far["offset_bits"], 16)
        self.assertEqual(far["serialized_bytes"], 4)

    def test_rtc_path_is_preserved(self):
        rom = self.cfg["rom"]
        self.assertTrue(rom["require_rtc_preservation"])
        self.assertEqual(rom["expanded_mapper"], "undecided")


if __name__ == "__main__":
    unittest.main()
