"""Unit tests for Guidebook Generator using stdlib unittest."""
import os
import sys
import json
import tempfile
import unittest
from pathlib import Path
from PIL import Image

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

import guidebook
from guidebook import GuidebookBuilder, validate_spec, rectangle_pixels

class TestGuidebook(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.work_dir = Path(self.temp_dir.name)

        # Create a valid synthetic dummy image
        self.dummy_img = self.work_dir / "screen.png"
        im = Image.new("RGB", (640, 480), "#1e293b")
        im.save(self.dummy_img)

        # Minimal valid spec
        self.valid_spec = {
            "title": "Aplikasi Uji",
            "organization": "Divisi QA",
            "slides": [
                {
                    "type": "cover",
                    "title": "Cover Panduan",
                    "description": "Deskripsi singkat pengujian."
                },
                {
                    "type": "step",
                    "step_number": 1,
                    "title": "Langkah Awal",
                    "screenshot": "screen.png",
                    "actions": ["Klik tombol simpan"],
                    "callouts": [{"box": [10, 10, 50, 30], "color": "accent"}]
                },
                {
                    "type": "outro",
                    "title": "Penutup Panduan",
                    "message": "Selesai"
                }
            ]
        }

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_rectangle_pixels_percent(self):
        box = rectangle_pixels([10, 20, 30, 40], (1000, 500), units="percent")
        self.assertEqual(box, (100, 100, 400, 300))

    def test_rectangle_pixels_auto(self):
        # Coordinates <= 100 infer percent in auto
        box = rectangle_pixels([20, 20, 50, 50], (800, 600), units="auto")
        self.assertEqual(box, (160, 120, 560, 420))

    def test_rectangle_pixels_bounds_guard(self):
        with self.assertRaises(ValueError):
            rectangle_pixels([-1, 0, 10, 10], (100, 100))
        with self.assertRaises(ValueError):
            rectangle_pixels([10, 10, 0, 10], (100, 100))
        with self.assertRaises(ValueError):
            rectangle_pixels([90, 90, 20, 20], (100, 100), units="percent")

    def test_validation_valid_spec(self):
        validated = validate_spec(self.valid_spec, self.work_dir)
        self.assertIsInstance(validated, dict)

    def test_validation_missing_screenshot(self):
        bad_spec = {
            "title": "Test",
            "slides": [
                {"type": "step", "title": "Step 1", "screenshot": "non_existent.png"}
            ]
        }
        with self.assertRaises(ValueError):
            validate_spec(bad_spec, self.work_dir)

    def test_validation_corrupt_screenshot(self):
        corrupt_file = self.work_dir / "corrupt.png"
        corrupt_file.write_bytes(b"NOT_AN_IMAGE_FILE_DATA_12345")
        bad_spec = {
            "title": "Test",
            "slides": [
                {"type": "step", "title": "Step 1", "screenshot": "corrupt.png"}
            ]
        }
        with self.assertRaises(ValueError):
            validate_spec(bad_spec, self.work_dir)

    def test_validation_invalid_slide_type(self):
        bad_spec = {
            "title": "Test",
            "slides": [
                {"type": "unsupported_type_xyz"}
            ]
        }
        with self.assertRaises(ValueError):
            validate_spec(bad_spec, self.work_dir)

    def test_html_injection_escaping(self):
        malicious_spec = {
            "title": "<script>alert('xss')</script>",
            "organization": "<img src=x onerror=alert(1)>",
            "slides": [
                {"type": "cover", "title": "Safe Slide"}
            ]
        }
        builder = GuidebookBuilder(malicious_spec, base_dir=str(self.work_dir))
        html_out = self.work_dir / "index.html"
        builder.build_html(str(html_out), image_dir_rel="slides")

        content = html_out.read_text(encoding="utf-8")
        self.assertNotIn("<script>alert('xss')</script>", content)
        self.assertNotIn("<img src=x onerror=alert(1)>", content)
        self.assertIn("&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;", content)
        self.assertIn("&lt;img src=x onerror=alert(1)&gt;", content)

    def test_build_pdf_and_reopen(self):
        builder = GuidebookBuilder(self.valid_spec, base_dir=str(self.work_dir))
        pdf_out = self.work_dir / "output.pdf"
        builder.build_pdf(str(pdf_out))
        self.assertTrue(pdf_out.exists())
        self.assertGreater(pdf_out.stat().st_size, 1000)

        # Validate reopening using pymupdf
        try:
            try:
                import pymupdf as fitz
            except ImportError:
                import fitz
            doc = fitz.open(str(pdf_out))
            self.assertEqual(len(doc), 3)
            doc.close()
        except ImportError:
            # Fallback to Pillow verification
            im = Image.open(pdf_out)
            self.assertTrue(im.is_animated or getattr(im, "n_frames", 1) >= 1)

    def test_html_relative_path(self):
        builder = GuidebookBuilder(self.valid_spec, base_dir=str(self.work_dir))
        html_out = self.work_dir / "deck" / "index.html"
        builder.build_html(str(html_out), image_dir_rel="../slides")
        content = html_out.read_text(encoding="utf-8")
        self.assertIn('src="../slides/slide-01.png"', content)
        self.assertIn('`../slides/slide-${numStr}.png`', content)

if __name__ == "__main__":
    unittest.main()
