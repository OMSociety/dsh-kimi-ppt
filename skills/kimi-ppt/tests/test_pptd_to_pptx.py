#!/usr/bin/env python3
"""pptd_to_pptx.py 行为测试：fit/crop 渲染链、line 坐标映射、table 最小样式映射、
dropped 降级清单、空 deck fail-fast、形状映射名。

数学部分走纯函数单测；渲染链与 XML 结果走夹具端到端（临时目录造 deck，解导出 XML）。
"""
import contextlib
import importlib.util
import io
import tempfile
import unittest
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from unittest.mock import patch

from PIL import Image


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "pptd_to_pptx.py"
SPEC = importlib.util.spec_from_file_location("pptd_to_pptx", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)

A = "http://schemas.openxmlformats.org/drawingml/2006/main"
P = "http://schemas.openxmlformats.org/presentationml/2006/main"

THEME = """version: "v2"
size: [960, 540]
theme:
  colors:
    primary: "#0066B3"
    accent: "#FFC300"
  textStyles:
    body: {fontSize: 20, color: "$primary", bold: true}
  tableStyles:
    default:
      cellStyle: {fontSize: 12}
      firstRowStyle: {fontSize: 20, bold: true, fill: {type: solid, color: "$accent"}}
pages:
  - pages/p1.page
"""


def write_deck(root, page_body, theme=THEME):
    root = Path(root)
    (root / "pages").mkdir(parents=True, exist_ok=True)
    (root / "media").mkdir(exist_ok=True)
    Image.new("RGB", (400, 200), (255, 0, 0)).save(root / "media" / "wide.png")
    (root / "deck.pptd").write_text(theme, encoding="utf-8")
    (root / "pages" / "p1.page").write_text(page_body, encoding="utf-8")
    return root


def run_main(root):
    out = Path(root) / "out.pptx"
    err = io.StringIO()
    with patch.object(
        MODULE.sys,
        "argv",
        ["pptd_to_pptx.py", str(Path(root) / "deck.pptd"), "-o", str(out), "--force"],
    ), contextlib.redirect_stderr(err):
        MODULE.main()
    return out, err.getvalue()


def slide_root(path):
    with zipfile.ZipFile(path) as archive:
        return ET.fromstring(archive.read("ppt/slides/slide1.xml"))


def first_pic(root):
    return root.find(f".//{{{P}}}pic")


def src_rect(pic):
    return pic.find(f".//{{{P}}}blipFill/{{{A}}}srcRect")


class FitMathTests(unittest.TestCase):
    def test_cover_wide_image_crops_left_right(self):
        (left, top, right, bottom), width, height = MODULE._fit_rect(
            400, 200, 200, 200, 0, 0, 0, 0, "cover")
        self.assertAlmostEqual(left, 0.25)
        self.assertAlmostEqual(right, 0.25)
        self.assertEqual((top, bottom), (0, 0))
        self.assertEqual((width, height), (200, 200))

    def test_cover_tall_image_crops_top_bottom(self):
        (left, top, right, bottom), width, height = MODULE._fit_rect(
            100, 200, 200, 200, 0, 0, 0, 0, "cover")
        self.assertAlmostEqual(top, 0.25)
        self.assertAlmostEqual(bottom, 0.25)
        self.assertEqual((left, right), (0, 0))

    def test_cover_with_crop_combines_both(self):
        (left, top, right, bottom), _w, _h = MODULE._fit_rect(
            400, 200, 200, 200, 0, 0.1, 0, 0.1, "cover")
        self.assertAlmostEqual(left, 0.3)
        self.assertAlmostEqual(right, 0.3)
        self.assertAlmostEqual(top, 0.1)
        self.assertAlmostEqual(bottom, 0.1)

    def test_contain_shrinks_box_keeping_ratio(self):
        (_rect, width, height) = MODULE._fit_rect(400, 200, 200, 200, 0, 0, 0, 0, "contain")
        self.assertAlmostEqual(width, 200)
        self.assertAlmostEqual(height, 100)

    def test_fill_keeps_bounds(self):
        (_rect, width, height) = MODULE._fit_rect(400, 200, 200, 200, 0, 0, 0, 0, "fill")
        self.assertEqual((width, height), (200, 200))


class CropFractionTests(unittest.TestCase):
    def test_absent_crop_is_zero(self):
        self.assertEqual(MODULE._crop_fractions(None), (0.0, 0.0, 0.0, 0.0))

    def test_positive_crop_passes_through(self):
        self.assertEqual(MODULE._crop_fractions({"top": 0.1, "left": 0.2}),
                         (0.2, 0.1, 0.0, 0.0))

    def test_negative_outset_is_rejected(self):
        self.assertIsNone(MODULE._crop_fractions({"left": -0.1}))

    def test_degenerate_region_is_rejected(self):
        self.assertIsNone(MODULE._crop_fractions({"left": 0.6, "right": 0.5}))


class ShapeMapTests(unittest.TestCase):
    def test_documented_rt_triangle_resolves(self):
        self.assertIn("rtTriangle", MODULE.SHAPE_MAP)
        self.assertIsNot(MODULE.find_shape("rtTriangle"), MODULE.MSO_SHAPE.RECTANGLE)

    def test_unknown_shape_falls_back_to_rect(self):
        self.assertIs(MODULE.find_shape("notAShapeAtAll"), MODULE.MSO_SHAPE.RECTANGLE)


class ExportEndToEndTests(unittest.TestCase):
    IMG = ("elements:\n- elementId: im1\n  elementType: image\n  bounds: [0, 0, 100, 100]\n"
           "  src: media/wide.png\n")

    def test_cover_writes_src_rect(self):
        with tempfile.TemporaryDirectory() as name:
            write_deck(name, self.IMG)
            out, _err = run_main(name)
            rect = src_rect(first_pic(slide_root(out)))
        self.assertIsNotNone(rect)
        self.assertEqual((rect.get("l"), rect.get("r")), ("25000", "25000"))

    def test_contain_shrinks_picture_box(self):
        body = self.IMG.replace("src: media/wide.png", "src: media/wide.png\n  fit: {mode: contain}")
        with tempfile.TemporaryDirectory() as name:
            write_deck(name, body)
            out, _err = run_main(name)
            ext = first_pic(slide_root(out)).find(f".//{{{A}}}ext")
        self.assertEqual((int(ext.get("cx")), int(ext.get("cy"))), (1270000, 635000))

    def test_crop_outset_degrades_with_note(self):
        body = self.IMG.replace("src: media/wide.png", "src: media/wide.png\n  crop: {left: -0.1}")
        with tempfile.TemporaryDirectory() as name:
            write_deck(name, body)
            _out, err = run_main(name)
        self.assertIn("crop outset", err)

    def test_empty_pages_fail_fast(self):
        with tempfile.TemporaryDirectory() as name:
            write_deck(name, self.IMG, theme=THEME.replace(
                "pages:\n  - pages/p1.page\n", "pages: []\n"))
            with self.assertRaises(SystemExit) as caught:
                run_main(name)
        self.assertNotEqual(caught.exception.code, 0)
        self.assertIn("必须非空", str(caught.exception.code))

    def test_table_header_uses_theme_style(self):
        body = ("elements:\n- elementId: tb1\n  elementType: table\n  bounds: [0, 0, 300, 100]\n"
                "  columnWidths: [0.5, 0.5]\n  rowHeights: [0.5, 0.5]\n  style: \"$default\"\n"
                "  rows:\n    - - {text: H1}\n      - {text: H2}\n    - - {text: a}\n      - {text: b}\n")
        with tempfile.TemporaryDirectory() as name:
            write_deck(name, body)
            out, _err = run_main(name)
            root = slide_root(out)
        first_row = root.find(f".//{{{A}}}tbl/{{{A}}}tr")
        run_props = first_row.find(f".//{{{A}}}rPr")
        fill = first_row.find(f".//{{{A}}}tcPr/{{{A}}}solidFill/{{{A}}}srgbClr")
        self.assertEqual(run_props.get("sz"), "2000")
        self.assertIsNotNone(fill)
        self.assertEqual(fill.get("val"), "FFC300")

    def test_shape_without_fill_gets_no_fill(self):
        body = ("elements:\n- elementId: s1\n  elementType: shape\n  bounds: [0, 0, 50, 50]\n"
                "  shapeName: rect\n")
        with tempfile.TemporaryDirectory() as name:
            write_deck(name, body)
            out, _err = run_main(name)
            no_fill = slide_root(out).find(f".//{{{P}}}sp/{{{P}}}spPr/{{{A}}}noFill")
        self.assertIsNotNone(no_fill)

    def test_dropped_reasons_reported(self):
        body = ("elements:\n- elementId: ic1\n  elementType: icon\n  bounds: [0, 0, 20, 20]\n"
                "- elementId: s1\n  elementType: shape\n  bounds: [0, 0, 20, 20]\n"
                "  shapeName: bogusShape\n  opacity: 0.5\n")
        with tempfile.TemporaryDirectory() as name:
            write_deck(name, body)
            _out, err = run_main(name)
        self.assertIn("icon/ic1", err)
        self.assertIn("opacity", err)
        self.assertIn("unknown shapeName", err)
        self.assertIn("dropped total:", err)


if __name__ == "__main__":
    unittest.main()
