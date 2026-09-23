from __future__ import annotations

import hashlib
import unittest
from pathlib import Path

from tools.decode_legacy_save import RAW_SRAM_BYTES, checksum16, load_layouts, stored_box_offsets
from tools.import_legacy_silver import import_legacy_pair

ROOT = Path(__file__).resolve().parents[1]

class LegacyPairImportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.layouts = load_layouts(ROOT / "config" / "legacy_save_layouts.json")

    def make_rom(self, title: str, revision: int, size: int) -> bytes:
        data = bytearray(size)
        data[0x134:0x134+len(title)] = title.encode("ascii")
        data[0x147] = 0x10
        data[0x149] = 0x03
        data[0x14C] = revision
        return bytes(data)

    def make_save(self, profile: str) -> bytes:
        layout = self.layouts[profile]
        data = bytearray(RAW_SRAM_BYTES)
        party = layout["party"]
        data[party["file_offset"]] = 0
        data[party["file_offset"]+1] = 0xFF
        active = layout["active_box"]
        data[active["file_offset"]] = 0
        data[active["file_offset"]+1] = 0xFF
        for offset in stored_box_offsets(layout):
            data[offset] = 0
            data[offset+1] = 0xFF
        cv = layout["check_values"]
        data[cv["first_offset"]] = cv["first_value"]
        data[cv["second_offset"]] = cv["second_value"]
        cs = layout["primary_checksum"]
        value = checksum16(data, cs["start"], cs["end_inclusive"])
        data[cs["stored_offset"]:cs["stored_offset"]+2] = value.to_bytes(2, "little")
        return bytes(data)

    def test_rom_selects_exact_release_save_decoder(self):
        cases = (
            ("POKEMON_SLVAAXJ",0,1024*1024,"jp-rev0"),
            ("POKEMON_SLVAAXJ",1,1024*1024,"jp-rev1"),
            ("POKEMON_SLVAAXK",0,2*1024*1024,"ko-rev0"),
            ("POKEMON_SLVAAXE",0,2*1024*1024,"en-rev0"),
            ("POKEMON_SLVAAXD",0,2*1024*1024,"de-rev0"),
            ("POKEMON_SLVAAXF",0,2*1024*1024,"fr-rev0"),
            ("POKEMON_SLVAAXI",0,2*1024*1024,"it-rev0"),
            ("POKEMON_SLVAAXS",0,2*1024*1024,"es-rev0"),
        )
        for title,revision,size,profile in cases:
            with self.subTest(profile=profile):
                rom = self.make_rom(title, revision, size)
                save = self.make_save(profile)
                payload = import_legacy_pair(
                    rom, save,
                    require_retail_rom=False,
                    layouts=self.layouts,
                    audited_save_hashes={profile: hashlib.sha256(save).hexdigest()},
                )
                self.assertEqual(payload["source"]["profile_id"], profile)
                self.assertEqual(payload["gba_import"]["source_profile"], profile)
                self.assertTrue(payload["source"]["primary_save_valid"])
                self.assertTrue(payload["source"]["supplied_audit_sample_save_match"])

    def test_invalid_primary_save_is_rejected(self):
        rom = self.make_rom("POKEMON_SLVAAXE",0,2*1024*1024)
        save = bytearray(self.make_save("en-rev0"))
        save[0x2009] ^= 1
        with self.assertRaises(ValueError):
            import_legacy_pair(
                rom, bytes(save),
                require_retail_rom=False,
                layouts=self.layouts,
                audited_save_hashes={},
            )

    def test_audited_sample_hash_is_provenance_not_format_requirement(self):
        rom = self.make_rom("POKEMON_SLVAAXE",0,2*1024*1024)
        save = self.make_save("en-rev0")
        payload = import_legacy_pair(
            rom, save,
            require_retail_rom=False,
            layouts=self.layouts,
            audited_save_hashes={"en-rev0":"00"*32},
        )
        self.assertFalse(payload["source"]["supplied_audit_sample_save_match"])
        self.assertTrue(payload["source"]["primary_save_valid"])

if __name__ == "__main__":
    unittest.main()
