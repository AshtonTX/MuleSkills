#!/usr/bin/env python3
"""Check the guardrail files before they are shared or installed.

Checks:
  - every scoped instruction file starts with front matter that sets `applyTo`
  - the skill's front matter has a `name` matching its folder and a `description`
  - every relative Markdown link in the repository points to a file that exists
  - links inside overlay/ stay inside overlay/, so the files still work after
    they are copied into a Mule project

Uses only the Python standard library (3.9 or later). Exit code 0 means every
check passed. It does not run Mule, DataWeave, MUnit or Copilot.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OVERLAY = ROOT / "overlay"
LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
FRONT_MATTER = re.compile(r"\A---\n(.*?)\n---\n", re.S)

REQUIRED = [
    ".github/copilot-instructions.md",
    ".github/instructions/dataweave.instructions.md",
    ".github/instructions/maven.instructions.md",
    ".github/instructions/mule-xml.instructions.md",
    ".github/instructions/munit.instructions.md",
    ".github/skills/team-mule-guardrails/SKILL.md",
    ".github/mule/team-profile.md",
    ".github/mule/task-recipes.md",
]


def front_matter(text):
    match = FRONT_MATTER.match(text)
    if not match:
        return None
    fields = {}
    for line in match.group(1).splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            fields[key.strip()] = value.strip().strip('"')
    return fields


def main():
    errors = []

    for rel in REQUIRED:
        if not (OVERLAY / rel).is_file():
            errors.append(f"missing overlay file: overlay/{rel}")

    for path in sorted((OVERLAY / ".github/instructions").glob("*.instructions.md")):
        fields = front_matter(path.read_text(encoding="utf-8"))
        if not fields or not fields.get("applyTo"):
            errors.append(f"{path.relative_to(ROOT)}: front matter must set applyTo")

    for skill in sorted((OVERLAY / ".github/skills").glob("*/SKILL.md")):
        fields = front_matter(skill.read_text(encoding="utf-8")) or {}
        if fields.get("name") != skill.parent.name:
            errors.append(f"{skill.relative_to(ROOT)}: name must be '{skill.parent.name}'")
        if not fields.get("description"):
            errors.append(f"{skill.relative_to(ROOT)}: description is required")

    for path in sorted(ROOT.rglob("*.md")):
        if ".git" in path.parts:
            continue
        text = path.read_text(encoding="utf-8")
        for target in LINK.findall(text):
            if re.match(r"^[a-z][a-z0-9+.-]*:", target) or target.startswith("#"):
                continue
            file_part = target.split("#", 1)[0]
            resolved = (path.parent / file_part).resolve()
            where = path.relative_to(ROOT)
            if not resolved.exists():
                errors.append(f"{where}: broken link {target}")
            elif OVERLAY in path.parents and OVERLAY not in resolved.parents:
                errors.append(f"{where}: link leaves overlay/ and will break after install: {target}")

    if errors:
        print("FAILED")
        for error in errors:
            print(f"  - {error}")
        return 1
    print(f"OK: {len(REQUIRED)} overlay files present; front matter and links valid")
    return 0


if __name__ == "__main__":
    sys.exit(main())
