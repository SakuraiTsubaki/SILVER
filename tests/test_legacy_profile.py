from __future__ import annotations

import unittest

from tools.detect_legacy_profile import detect_rom, inspect_save

class LegacyProfileDetectionTests(unittest.TestCase):
    def make_rom(self, title: str, revision: int = 0, size: int = 2 * 1024 * 1024) -> bytes:
        data = bytearray(size)
        encoded = title.encode("ascii")
        data[0x134:0x134 + len(encoded)] = encoded
        data[0x147] = 0x10
        data[0x149] = 0x03
        data[0x14C] = revision
        return bytes(data)

    def test_japanese_revision_detection(self):
        result = detect_rom(self.make_rom("POKEMON_SLVAAXJ", revision=1, size=1024 * 1024))
        self.assertEqual(result["profile"], "jp")
        self.assertEqual(result["revision"], 1)
        self.assertEqual(result["rom_bytes"], 1024 * 1024)

    def test_korean_detection(self):
        self.assertEqual(detect_rom(self.make_rom("POKEMON_SLVAAXK"))["profile"], "ko")

    def test_western_languages_share_layout_profile(self):
        for title in ("POKEMON_SLVAAXE", "POKEMON_SLVAAXD", "POKEMON_SLVAAXF", "POKEMON_SLVAAXI", "POKEMON_SLVAAXS"):
            with self.subTest(title=title):
                self.assertEqual(detect_rom(self.make_rom(title))["profile"], "western")

    def test_wrong_mapper_is_rejected(self):
        rom = bytearray(self.make_rom("POKEMON_SLVAAXE"))
        rom[0x147] = 0x1B
        with self.assertRaises(ValueError):
            detect_rom(bytes(rom))

    def test_save_separates_raw_sram_from_host_tail(self):
        result = inspect_save(bytes(32768 + 44))
        self.assertEqual(result["raw_sram_bytes"], 32768)
        self.assertEqual(result["trailing_host_bytes"], 44)

if __name__ == "__main__":
    unittest.main()
