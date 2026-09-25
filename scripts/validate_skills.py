#!/usr/bin/env python3
"""Validate the portable Agent Skills metadata without external dependencies."""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / ".agents" / "skills"
NAME = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def validate(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    parts = text.split("---", 2)
    if len(parts) != 3 or parts[0].strip():
        raise ValueError(f"{path}: missing YAML frontmatter")
    fields = {}
    for line in parts[1].splitlines():
        if not line.strip():
            continue
        key, separator, value = line.partition(":")
        if not separator or not value.strip():
            raise ValueError(f"{path}: malformed frontmatter line")
        fields[key.strip()] = value.strip()
    name = fields.get("name", "")
    description = fields.get("description", "")
    if not NAME.fullmatch(name) or name != path.parent.name or len(name) > 64:
        raise ValueError(f"{path}: invalid name")
    if not 1 <= len(description) <= 1024:
        raise ValueError(f"{path}: invalid description")
    if fields.get("license") != "MIT":
        raise ValueError(f"{path}: license should match repository")
    if not parts[2].strip():
        raise ValueError(f"{path}: empty body")


def main() -> None:
    paths = sorted(SKILLS.glob("*/SKILL.md"))
    if not paths:
        raise ValueError("No skills found")
    for path in paths:
        validate(path)
    print(f"Validated {len(paths)} Agent Skills")


if __name__ == "__main__":
    main()
