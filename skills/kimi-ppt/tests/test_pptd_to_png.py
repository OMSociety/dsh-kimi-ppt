#!/usr/bin/env python3
"""pptd_to_png.py 行为测试：viewBox→bounds 坐标映射、image fit/crop 三模式、
rotation 绘制、custom 灰描边、无填充语义、dropped 清单、空 deck fail-fast。

渲染结果做像素级断言（左绿右蓝双色夹具可区分裁切与留白）。
"""
import contextlib
import importlib.util
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "pptd_to_png.py"
SPEC = importlib.util.spec_from_file_location("pptd_to_png", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)

GREEN, BLUE, RED, WHITE = (0, 255, 0), (0, 0, 255), (255, 0, 0), (255, 255, 255)

THEME = 'version: "v2"\nsize: [960, 540]\ntheme:\n  colors: {primary: "#0066B3"}\npages:\n  - pages/p1.page\n'


def write_deck(root, page_body, theme=THEME):
    root = Path(root)
    (root / "pages").mkdir(parents=True, exist_ok=True)
    (root / "media").mkdir(exist_ok=True)
    image = Image.new("RGB", (400, 200))
    image.paste(GREEN, (0, 0, 200, 200))
    image.paste(BLUE, (200, 0, 400, 200))
    image.save(root / "media" / "two.png")
    (root / "deck.pptd").write_text(theme, encoding="utf-8")
    (root / "pages" / "p1.page").write_text(page_body, encoding="utf-8")
    return root


def run_main(root, scale=1):
    out_dir = Path(root) / "out"
    err = io.StringIO()
    with patch.object(
        MODULE.sys,
        "argv",
        ["pptd_to_png.py", str(Path(root) / "deck.pptd"), "-o", str(out_dir), "--scale", str(scale)],
    ), contextlib.redirect_stderr(err):
        MODULE.main()
    return out_dir / "page_1.png", err.getvalue()


def pixels(path):
    return Image.open(path).convert("RGB")


def assert_near(case, actual, expected, tol=40):
    case.assertTrue(all(abs(a - b) <= tol for a, b in zip(actual, expected)), (actual, expected))


class CropFractionTests(unittest.TestCase):
    def test_negative_outset_is_rejected(self):
        self.assertIsNone(MODULE._crop_fractions({"top": -0.2}))

    def test_absent_crop_is_zero(self):
        self.assertEqual(MODULE._crop_fractions(None), (0.0, 0.0, 0.0, 0.0))


class RenderTests(unittest.TestCase):
    IMG = ("elements:\n- elementId: im1\n  elementType: image\n  bounds: [0, 0, 200, 200]\n"
           "  src: media/two.png\n")

    def test_cover_crops_centered(self):
        with tempfile.TemporaryDirectory() as name:
            write_deck(name, self.IMG)
            path, _err = run_main(name)
            image = pixels(path)
        assert_near(self, image.getpixel((50, 100)), GREEN)
        assert_near(self, image.getpixel((150, 100)), BLUE)

    def test_fill_stretches(self):
        body = self.IMG.replace("src: media/two.png", "src: media/two.png\n  fit: {mode: fill}")
        with tempfile.TemporaryDirectory() as name:
            write_deck(name, body)
            path, _err = run_main(name)
            image = pixels(path)
        assert_near(self, image.getpixel((50, 100)), GREEN)
        assert_near(self, image.getpixel((150, 100)), BLUE)

    def test_contain_letterboxes(self):
        body = self.IMG.replace("src: media/two.png", "src: media/two.png\n  fit: {mode: contain}")
        with tempfile.TemporaryDirectory() as name:
            write_deck(name, body)
            path, _err = run_main(name)
            image = pixels(path)
        assert_near(self, image.getpixel((100, 20)), WHITE)
        assert_near(self, image.getpixel((50, 100)), GREEN)

    def test_line_maps_viewbox_to_bounds(self):
        body = ("elements:\n- elementId: ln1\n  elementType: line\n  bounds: [100, 100, 200, 100]\n"
                "  viewBox: [1000, 500]\n  points: \"0,0 1000,500\"\n"
                "  border: {style: solid, width: 3, color: \"#FF0000\"}\n")
        for scale, point in ((1, (200, 150)), (4, (800, 600))):
            with tempfile.TemporaryDirectory() as name:
                write_deck(name, body)
                path, _err = run_main(name, scale=scale)
                sample = pixels(path).getpixel(point)
            assert_near(self, sample, RED)

    def test_rotation_changes_pixels(self):
        body = ("elements:\n- elementId: s1\n  elementType: shape\n  bounds: [100, 100, 200, 200]\n"
                "  shapeName: triangle\n  fill: {type: solid, color: \"#FF0000\"}\n")
        with tempfile.TemporaryDirectory() as name:
            write_deck(name, body)
            path0, _err = run_main(name)
            plain = pixels(path0)
        with tempfile.TemporaryDirectory() as name:
            write_deck(name, body.replace("color: \"#FF0000\"}", "color: \"#FF0000\"}\n  rotation: 90"))
            path90, _err = run_main(name)
            rotated = pixels(path90)
        diff = sum(1 for a, b in zip(plain.tobytes(), rotated.tobytes()) if a != b)
        self.assertGreater(diff, 500)
        assert_near(self, rotated.getpixel((200, 200)), RED)

    def test_shape_without_fill_draws_background(self):
        body = ("elements:\n- elementId: s2\n  elementType: shape\n  bounds: [50, 50, 100, 100]\n"
                "  shapeName: rect\n")
        with tempfile.TemporaryDirectory() as name:
            write_deck(name, body)
            path, _err = run_main(name)
            sample = pixels(path).getpixel((100, 100))
        assert_near(self, sample, WHITE)

    def test_custom_is_hollow_gray_outline(self):
        body = ("elements:\n- elementId: s3\n  elementType: shape\n  bounds: [50, 50, 100, 100]\n"
                "  shapeName: custom\n  fill: {type: solid, color: \"#FF0000\"}\n")
        with tempfile.TemporaryDirectory() as name:
            write_deck(name, body)
            path, _err = run_main(name)
            image = pixels(path)
            center, edge = image.getpixel((100, 100)), image.getpixel((50, 50))
        assert_near(self, center, WHITE)
        assert_near(self, edge, (136, 136, 136), tol=60)


class FailureTests(unittest.TestCase):
    def test_empty_pages_fail_fast(self):
        with tempfile.TemporaryDirectory() as name:
            write_deck(name, "", theme=THEME.replace("pages:\n  - pages/p1.page\n", "pages: []\n"))
            with self.assertRaises(SystemExit) as caught:
                run_main(name)
        self.assertNotEqual(caught.exception.code, 0)
        self.assertIn("必须非空", str(caught.exception.code))

    def test_dropped_reasons_reported(self):
        body = ("elements:\n- elementId: ic1\n  elementType: icon\n  bounds: [0, 0, 20, 20]\n"
                "- elementId: tb1\n  elementType: table\n  bounds: [0, 0, 20, 20]\n"
                "- elementId: s1\n  elementType: shape\n  bounds: [0, 0, 20, 20]\n"
                "  shapeName: star5\n  opacity: 0.5\n  flip: [true, false]\n")
        with tempfile.TemporaryDirectory() as name:
            write_deck(name, body)
            _path, err = run_main(name)
        self.assertIn("icon/ic1", err)
        self.assertIn("table/tb1", err)
        self.assertIn("opacity", err)
        self.assertIn("flip not supported", err)
        self.assertIn("dropped total:", err)


if __name__ == "__main__":
    unittest.main()
