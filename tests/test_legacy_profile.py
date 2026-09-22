from __future__ import annotations
import unittest
from tools.detect_legacy_profile import detect_rom, inspect_save

class LegacyProfileDetectionTests(unittest.TestCase):
    CASES = (
        ("POKEMON_SLVAAXJ",0,1024*1024,"jp-rev0"),
        ("POKEMON_SLVAAXJ",1,1024*1024,"jp-rev1"),
        ("POKEMON_SLVAAXK",0,2*1024*1024,"ko-rev0"),
        ("POKEMON_SLVAAXE",0,2*1024*1024,"en-rev0"),
        ("POKEMON_SLVAAXD",0,2*1024*1024,"de-rev0"),
        ("POKEMON_SLVAAXF",0,2*1024*1024,"fr-rev0"),
        ("POKEMON_SLVAAXI",0,2*1024*1024,"it-rev0"),
        ("POKEMON_SLVAAXS",0,2*1024*1024,"es-rev0"),
    )

    def make_rom(self, title: str, revision: int, size: int) -> bytes:
        data=bytearray(size)
        data[0x134:0x134+len(title)] = title.encode("ascii")
        data[0x147]=0x10
        data[0x149]=0x03
        data[0x14C]=revision
        return bytes(data)

    def test_all_eight_releases_are_distinct_profiles(self):
        seen=set()
        for title,revision,size,profile in self.CASES:
            with self.subTest(profile=profile):
                result=detect_rom(self.make_rom(title,revision,size),require_baseline_hash=False)
                self.assertEqual(result["profile"],profile)
                seen.add(result["profile"])
        self.assertEqual(len(seen),8)

    def test_no_western_collapse_profile_exists(self):
        profiles={detect_rom(self.make_rom(t,r,s),require_baseline_hash=False)["profile"] for t,r,s,_ in self.CASES}
        self.assertNotIn("western",profiles)
        self.assertNotIn("jp",profiles)
        self.assertNotIn("ko",profiles)

    def test_wrong_mapper_is_rejected(self):
        rom=bytearray(self.make_rom("POKEMON_SLVAAXE",0,2*1024*1024))
        rom[0x147]=0x1B
        with self.assertRaises(ValueError):
            detect_rom(bytes(rom))

    def test_wrong_size_is_rejected(self):
        with self.assertRaises(ValueError):
            detect_rom(self.make_rom("POKEMON_SLVAAXJ",0,2*1024*1024))

    def test_save_separates_four_sram_banks_and_tail(self):
        result=inspect_save(bytes(32768+44))
        self.assertEqual(result["raw_sram_bytes"],32768)
        self.assertEqual(result["trailing_host_bytes"],44)
        self.assertEqual(len(result["sram_bank_sha256"]),4)

if __name__=="__main__":
    unittest.main()
