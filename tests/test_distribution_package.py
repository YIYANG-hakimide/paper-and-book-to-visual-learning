from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ROOT = ROOT / "plugins" / "paper-and-book-to-visual-learning"
SKILL_ROOT = PLUGIN_ROOT / "skills" / "paper-and-book-to-visual-learning"


class DistributionPackageTests(unittest.TestCase):
    def test_plugin_manifest_and_marketplace_names_match(self) -> None:
        manifest = json.loads((PLUGIN_ROOT / ".codex-plugin" / "plugin.json").read_text())
        marketplace = json.loads((ROOT / ".agents" / "plugins" / "marketplace.json").read_text())
        entry = marketplace["plugins"][0]
        self.assertEqual(manifest["name"], "paper-and-book-to-visual-learning")
        self.assertEqual(entry["name"], manifest["name"])
        self.assertEqual(entry["source"]["path"], "./plugins/paper-and-book-to-visual-learning")

    def test_generated_skill_matches_canonical_source(self) -> None:
        pairs = [
            (ROOT / "SKILL.md", SKILL_ROOT / "SKILL.md"),
            (ROOT / "LICENSE", SKILL_ROOT / "LICENSE.txt"),
            (ROOT / "assets" / "reader-runtime.js", SKILL_ROOT / "assets" / "reader-runtime.js"),
        ]
        for directory in ("agents", "references", "scripts"):
            for source in sorted((ROOT / directory).rglob("*")):
                if source.is_file() and "__pycache__" not in source.parts and source.suffix != ".pyc":
                    pairs.append((source, SKILL_ROOT / source.relative_to(ROOT)))

        for source, generated in pairs:
            with self.subTest(path=source.relative_to(ROOT)):
                self.assertTrue(generated.exists())
                self.assertEqual(source.read_bytes(), generated.read_bytes())


if __name__ == "__main__":
    unittest.main()
