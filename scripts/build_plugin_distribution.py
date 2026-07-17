#!/usr/bin/env python3
"""Build the committed Skill-only Plugin distribution from the canonical root Skill."""

from __future__ import annotations

import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ROOT = ROOT / "plugins" / "paper-and-book-to-visual-learning"
SKILL_ROOT = PLUGIN_ROOT / "skills" / "paper-and-book-to-visual-learning"


def replace_tree(source: Path, destination: Path) -> None:
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(source, destination, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))


def main() -> int:
    SKILL_ROOT.mkdir(parents=True, exist_ok=True)
    for directory in ("agents", "references", "scripts"):
        replace_tree(ROOT / directory, SKILL_ROOT / directory)

    assets_destination = SKILL_ROOT / "assets"
    if assets_destination.exists():
        shutil.rmtree(assets_destination)
    assets_destination.mkdir(parents=True)
    shutil.copy2(ROOT / "assets" / "reader-runtime.js", assets_destination / "reader-runtime.js")

    shutil.copy2(ROOT / "SKILL.md", SKILL_ROOT / "SKILL.md")
    shutil.copy2(ROOT / "LICENSE", SKILL_ROOT / "LICENSE.txt")
    shutil.copy2(ROOT / "LICENSE", PLUGIN_ROOT / "LICENSE")
    print(SKILL_ROOT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
