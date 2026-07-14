from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class AuditContractTests(unittest.TestCase):
    def test_strict_visual_audit_requires_source(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            result = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "audit_visual_series.py"), temp_dir, "--strict"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=30,
            )
        payload = json.loads(result.stdout)
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(any("requires --source" in issue for issue in payload["errors"]))

    def test_album_pdf_order_is_verified_against_numbered_images(self) -> None:
        audit = load_module("audit_visual_series", ROOT / "scripts" / "audit_visual_series.py")
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            image_dir = temp / "images"
            image_dir.mkdir()
            paths = []
            for index, color in enumerate(((190, 40, 40), (30, 100, 190)), 1):
                path = image_dir / f"{index:03d}-page.png"
                image = Image.new("RGB", (900, 1200), color)
                ImageDraw.Draw(image).text((80, 80), f"PAGE {index}", fill="white")
                image.save(path)
                paths.append(path)
            pdf_path = temp / "album.pdf"
            subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "build_image_album_pdf.py"),
                    str(image_dir),
                    str(pdf_path),
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=60,
            )
            self.assertEqual(audit.validate_album_pdf(pdf_path, 2, "3:4", paths, temp / "correct"), [])
            reversed_issues = audit.validate_album_pdf(pdf_path, 2, "3:4", list(reversed(paths)), temp / "reversed")
            self.assertTrue(any("does not visually match" in issue for issue in reversed_issues))


if __name__ == "__main__":
    unittest.main()
