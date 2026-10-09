#!/usr/bin/env python3
"""check_fonts.py unit tests.

Covers the pure functions (mapping, name normalization, matching, font
collection). The registry read in ``installed_families()`` is Windows-only and
deliberately not exercised here — it is covered indirectly by the CLI smoke
test in the skill's manual validation, not by unit tests.
"""
import importlib.util
import sys
import tempfile
import unittest
from io import StringIO
from pathlib import Path
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check_fonts.py"
SPEC = importlib.util.spec_from_file_location("check_fonts", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class CanonMappingTests(unittest.TestCase):
    def test_canonical_to_installed_spellings(self):
        # Known tricky mappings: the installed name is NOT always the canonical one.
        self.assertEqual(MODULE.CANON_TO_INSTALLED["QuattrocentoSans"], "Quattrocento Sans")
        self.assertEqual(MODULE.CANON_TO_INSTALLED["得意黑"], "得意黑 斜体")
        self.assertEqual(MODULE.CANON_TO_INSTALLED["霞鹜新致宋"], "霞鹜新致宋＋")
        self.assertEqual(MODULE.CANON_TO_INSTALLED["Source Han Serif"], "思源宋体 CN")
        self.assertEqual(MODULE.CANON_TO_INSTALLED["SimHei"], "SimHei")

    def test_unknown_name_passes_through(self):
        # A canonical name not in the map should be used as-is (no silent drop).
        self.assertEqual(MODULE.CANON_TO_INSTALLED.get("MadeUpWontExist", "MadeUpWontExist"), "MadeUpWontExist")


class NormalizeTests(unittest.TestCase):
    def test_strips_parenthesized_suffix_and_case(self):
        self.assertEqual(MODULE.normalize_req("MiSans (TrueType)"), "misans")
        self.assertEqual(MODULE.normalize_req("  MiSans  "), "misans")

    def test_blank_returns_blank(self):
        self.assertEqual(MODULE.normalize_req(""), "")
        self.assertEqual(MODULE.normalize_req("   "), "")


class PresentTests(unittest.TestCase):
    def _fams(self, *names):
        return {n.lower() for n in names}

    def test_exact_match(self):
        self.assertTrue(MODULE.present(self._fams("MiSans"), "MiSans"))

    def test_variant_suffix_still_match(self):
        # Installed "Courier New (TrueType)" normalizes to "courier new"; a
        # request for "courier new" must match even though the family name has
        # additional weight/variant entries.
        self.assertTrue(MODULE.present(self._fams("Courier New (TrueType)"), "Courier New"))

    def test_cjk_loose_prefix_match(self):
        # CJK names often carry the weight inside the family; the matcher is
        # deliberately loose (>=2 chars, family startswith the request).
        self.assertTrue(MODULE.present(self._fams("霞鹜文楷"), "霞鹜文楷"))

    def test_not_present(self):
        self.assertFalse(MODULE.present(self._fams("Arial"), "Georgia"))

    def test_empty_required_is_false(self):
        self.assertFalse(MODULE.present(self._fams("Arial"), ""))


class CollectFontsTests(unittest.TestCase):
    def _write_deck(self, root):
        deck = Path(root) / "deck.pptd"
        pages = Path(root) / "pages"
        pages.mkdir()
        page = (
            "version: v2\ntitle: t\nsize: [960, 540]\n"
            "theme:\n"
            "  textStyles:\n"
            "    title:\n"
            "      fontFamily:\n"
            "        latin: MiSans\n"
            "        ea: 思源宋体 CN\n"
            "pages:\n  - pages/01.page\n"
        )
        deck.write_text(page, encoding="utf-8")
        (pages / "01.page").write_text(
            "version: v2\npage: 1\nelements:\n"
            "  - type: text\n    content:\n      text: hi\n"
            "      fontFamily:\n        latin: MiSans\n        ea: 站酷文艺体\n"
            "  - type: text\n    content:\n      text: inline\n"
            "      fontFamily: Georgia\n",
            encoding="utf-8",
        )
        return deck

    def test_collects_theme_and_inline_fonts(self):
        with tempfile.TemporaryDirectory() as name:
            deck = self._write_deck(name)
            fonts = MODULE.collect_fonts(str(deck))
        self.assertEqual(fonts, {"MiSans", "思源宋体 CN", "站酷文艺体", "Georgia"})

    def test_missing_manifest_returns_empty(self):
        with tempfile.TemporaryDirectory() as name:
            # No theme.textStyles, no inline fontFamily -> empty set.
            deck = Path(name) / "empty.pptd"
            deck.write_text("version: v2\ntitle: t\nsize: [1, 1]\npages: []\n", encoding="utf-8")
            self.assertEqual(MODULE.collect_fonts(str(deck)), set())


class MainArgvTests(unittest.TestCase):
    def test_empty_invocation_errors(self):
        # Neither a manifest nor --fonts was given: the script must fail loudly
        # rather than silently report "all fonts available" for nothing.
        with patch.object(MODULE.sys, "argv", ["check_fonts.py"]), \
                self.assertRaises(SystemExit) as cm:
            MODULE.main()
        self.assertNotEqual(cm.exception.code, 0)

    def test_manifest_argument_collects_fonts(self):
        with tempfile.TemporaryDirectory() as name:
            deck = Path(name) / "deck.pptd"
            deck.write_text(
                "version: v2\ntitle: t\nsize: [1, 1]\n"
                "theme:\n  textStyles:\n    title:\n      fontFamily:\n        latin: MiSans\n"
                "pages: []\n",
                encoding="utf-8",
            )
            with patch.object(MODULE.sys, "argv", ["check_fonts.py", str(deck)]), \
                    patch.object(MODULE, "installed_families", return_value={"misans"}), \
                    patch.object(MODULE.sys, "stdout", StringIO()) as out:
                MODULE.main()
            captured = out.getvalue()
            self.assertIn("MiSans", captured)
            self.assertIn("[已装]", captured)



class WordBoundaryTests(unittest.TestCase):
    def _fams(self, *names):
        return {n.lower() for n in names}

    def test_bare_prefix_without_boundary_is_not_a_match(self):
        # "Literata" must not satisfy a request for "Liter" (the old loose
        # prefix matcher reported this as installed).
        self.assertFalse(MODULE.present(self._fams("literata"), "Liter"))

    def test_weight_suffix_after_space_matches(self):
        self.assertTrue(MODULE.present(self._fams("arial black"), "Arial"))

    def test_variant_suffix_after_hyphen_matches(self):
        self.assertTrue(MODULE.present(self._fams("arial-black"), "Arial"))

    def test_exact_casefold_match(self):
        self.assertTrue(MODULE.present(self._fams("literata"), "Literata"))


class _FakeWinreg:
    HKEY_LOCAL_MACHINE = "HKLM"
    HKEY_CURRENT_USER = "HKCU"

    def __init__(self, tables):
        self.tables = tables

    def OpenKey(self, root, _path):
        if root in self.tables:
            return root
        raise OSError(2, "registry key not found")

    def EnumValue(self, key, index):
        entries = self.tables[key]
        if index >= len(entries):
            raise OSError(259, "no more data")
        return (entries[index], "", 1)

    def CloseKey(self, _key):
        return None


class RegistryMergeTests(unittest.TestCase):
    def test_merges_hklm_and_hkcu(self):
        fake = _FakeWinreg({
            "HKLM": ["Arial (TrueType)"],
            "HKCU": ["Noto Sans SC Bold"],
        })
        with patch.dict(sys.modules, {"winreg": fake}):
            families = MODULE.installed_families()
        self.assertIn("arial", families)
        self.assertIn("noto sans sc bold", families)

    def test_duplicate_entries_collapse(self):
        fake = _FakeWinreg({
            "HKLM": ["Arial (TrueType)"],
            "HKCU": ["Arial (TrueType)"],
        })
        with patch.dict(sys.modules, {"winreg": fake}):
            families = MODULE.installed_families()
        self.assertEqual(families, {"arial"})

    def test_missing_hkcu_still_returns_hklm(self):
        fake = _FakeWinreg({"HKLM": ["Arial (TrueType)"]})
        with patch.dict(sys.modules, {"winreg": fake}):
            families = MODULE.installed_families()
        self.assertEqual(families, {"arial"})

    def test_missing_hklm_raises_for_posix_fallback(self):
        fake = _FakeWinreg({"HKCU": ["Arial (TrueType)"]})
        with patch.dict(sys.modules, {"winreg": fake}):
            with self.assertRaises(OSError):
                MODULE.installed_families()


if __name__ == "__main__":
    unittest.main()
