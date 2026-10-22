#!/usr/bin/env python3
"""Check the guardrail files before they are shared or installed.

Checks, for each layout under overlay/ (shared and github):
  - every scoped rule file starts with front matter that sets its scope key
    (`paths` in overlay/shared, `applyTo` in overlay/github) and a `description`,
    which Copilot shows the model beside the patterns
  - the skill's front matter has a `name` matching its folder and a `description`
  - inline relative Markdown links, with optional titles, point to existing paths
  - links inside a layout stay inside it, so the files still work after they
    are copied into a Mule project
  - every Markdown file is small enough for Copilot to read in one call

overlay/github is generated from overlay/shared; `scripts/build.py --check`
verifies that it is up to date.

Uses only the Python standard library (3.9 or later). Exit code 0 means every
check passed. It does not run Mule, DataWeave, MUnit or Copilot.

Front matter uses a deliberately small YAML subset: unindented, unique keys
with single-line string values. Plain values must start with a letter or
underscore and cannot be YAML booleans/null. Single quotes use YAML's doubled
apostrophes; double quotes use JSON-compatible escapes. Quote other values.
Comments and blank lines are allowed; collections and block scalars are not.
"""
import json
import re
import string
import sys
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parent.parent
OVERLAY = ROOT / "overlay"
LINK = re.compile(
    r"\[(?:[^\[\]\n]|\[[^\[\]\n]*\])*\]\("
    r"(?:<(?P<angle>[^<>\n]+)>|(?P<bare>(?:\\.|[^\s()\\]|\([^()\n]*\))+))"
    r"(?:\s+(?:\"(?:\\.|[^\"\\])*\"|'(?:\\.|[^'\\])*'|\([^()]*\)))?"
    r"\s*\)"
)
MARKDOWN_ESCAPE = re.compile(r"\\([" + re.escape(string.punctuation) + r"])")
FRONT_MATTER = re.compile(r"\A---\n(.*?)\n---(?:\n|\Z)", re.S)
FIELD = re.compile(r"([A-Za-z][A-Za-z0-9_-]*):(?:[ \t]+(.*))?")
NON_STRING = {"y", "n", "yes", "no", "true", "false", "on", "off", "null"}
# Copilot CLI and the Copilot desktop app do not inject scoped instruction files:
# the model opens them with a file-view tool that returns nothing but a
# "File too large" notice above 20 KiB (20,480 bytes; measured on CLI 1.0.96),
# and a ranged read cuts off whatever lies past that size. Stay well below it.
MAX_OVERLAY_FILE_BYTES = 18_000

RULES = ["api-contract", "configuration-properties", "dataweave", "maven", "mule-xml", "munit"]
SKILL_FILES = [
    "team-mule-guardrails/SKILL.md",
    "team-mule-guardrails/references/dataweave-correctness.md",
    "team-mule-guardrails/references/dataweave-operators.md",
    "team-mule-guardrails/references/dataweave-output-formats.md",
    "team-mule-guardrails/references/dataweave-performance.md",
    "team-mule-guardrails/references/mule-connectors.md",
    "team-mule-guardrails/references/mule-deployment-targets.md",
]
PROJECT_FILES = [
    ".github/mule/team-profile.md",
    ".github/mule/team-profile-guide.md",
    ".github/mule/task-recipes.md",
]
# Each layout: where scoped rules live, how their files are named, the
# front-matter key that scopes them, where skills live, and the files it must have.
LAYOUTS = {
    "shared": {
        "rules": ".claude/rules",
        "rule_glob": "*.md",
        "scope_key": "paths",
        "skills": ".claude/skills",
        "required": ["CLAUDE.md"]
        + [f".claude/rules/{name}.md" for name in RULES]
        + [f".claude/skills/{name}" for name in SKILL_FILES]
        + PROJECT_FILES,
    },
    "github": {
        "rules": ".github/instructions",
        "rule_glob": "*.instructions.md",
        "scope_key": "applyTo",
        "skills": ".github/skills",
        "required": [".github/copilot-instructions.md"]
        + [f".github/instructions/{name}.instructions.md" for name in RULES]
        + [f".github/skills/{name}" for name in SKILL_FILES]
        + PROJECT_FILES,
    },
}


def scalar(value):
    """Read one string in the documented YAML subset, rejecting ambiguity."""
    value = value.strip()
    if not value or value.startswith("#"):
        return ""
    if value.startswith('"'):
        match = re.fullmatch(r'("(?:[^"\\]|\\.)*")(?:[ \t]+#.*)?', value)
        if not match:
            raise ValueError("invalid double-quoted string")
        try:
            return json.loads(match.group(1))
        except ValueError as error:
            raise ValueError("double-quoted strings require JSON-compatible escapes") from error
    if value.startswith("'"):
        match = re.fullmatch(r"'((?:[^']|'')*)'(?:[ \t]+#.*)?", value)
        if not match:
            raise ValueError("invalid single-quoted string")
        return match.group(1).replace("''", "'")
    value = re.split(r"[ \t]+#", value, maxsplit=1)[0].rstrip()
    if not re.match(r"[A-Za-z_]", value) or re.search(r":(?:\s|$)", value):
        raise ValueError("use a quoted single-line string for this value")
    if value.lower() in NON_STRING:
        raise ValueError("metadata values must be strings, not YAML booleans/null")
    return value


def front_matter(text):
    match = FRONT_MATTER.match(text.replace("\r\n", "\n"))
    if not match:
        raise ValueError("front matter must start and end with --- lines")
    fields = {}
    for number, line in enumerate(match.group(1).splitlines(), start=2):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        field = FIELD.fullmatch(line)
        if not field:
            raise ValueError(f"line {number}: expected an unindented key: value field")
        key, value = field.groups()
        if key in fields:
            raise ValueError(f"line {number}: duplicate metadata key '{key}'")
        try:
            fields[key] = scalar(value or "")
        except ValueError as error:
            raise ValueError(f"line {number}: {error}") from error
    return fields


def main():
    errors = []

    for layout, spec in LAYOUTS.items():
        base = OVERLAY / layout
        for rel in spec["required"]:
            if not (base / rel).is_file():
                errors.append(f"missing overlay file: overlay/{layout}/{rel}")

        key = spec["scope_key"]
        for path in sorted((base / spec["rules"]).rglob(spec["rule_glob"])):
            try:
                fields = front_matter(path.read_text(encoding="utf-8"))
            except ValueError as error:
                errors.append(f"{path.relative_to(ROOT)}: {error}")
                continue
            patterns = fields.get(key, "").split(",")
            if any(not pattern.strip() for pattern in patterns):
                errors.append(f"{path.relative_to(ROOT)}: {key} must set nonempty glob patterns")
            if not fields.get("description", "").strip():
                errors.append(f"{path.relative_to(ROOT)}: description is required")

        for skill in sorted((base / spec["skills"]).glob("*/SKILL.md")):
            try:
                fields = front_matter(skill.read_text(encoding="utf-8"))
            except ValueError as error:
                errors.append(f"{skill.relative_to(ROOT)}: {error}")
                continue
            if fields.get("name") != skill.parent.name:
                errors.append(f"{skill.relative_to(ROOT)}: name must be '{skill.parent.name}'")
            if not fields.get("description", "").strip():
                errors.append(f"{skill.relative_to(ROOT)}: description is required")

    for path in sorted(OVERLAY.rglob("*.md")):
        size = path.stat().st_size
        if size > MAX_OVERLAY_FILE_BYTES:
            errors.append(
                f"{path.relative_to(ROOT)}: {size} bytes exceeds {MAX_OVERLAY_FILE_BYTES}; "
                "Copilot cannot read a larger file in one call, so move situational detail to a reference file"
            )

    for path in sorted(ROOT.rglob("*.md")):
        if ".git" in path.parts:
            continue
        text = path.read_text(encoding="utf-8")
        for match in LINK.finditer(text):
            target = MARKDOWN_ESCAPE.sub(r"\1", match.group("angle") or match.group("bare"))
            if re.match(r"^[a-z][a-z0-9+.-]*:", target, re.I) or target.startswith("#"):
                continue
            file_part = unquote(target.split("#", 1)[0].split("?", 1)[0])
            resolved = (path.parent / file_part).resolve()
            where = path.relative_to(ROOT)
            if not resolved.exists():
                errors.append(f"{where}: broken link {target}")
            else:
                for layout in LAYOUTS:
                    base = (OVERLAY / layout).resolve()
                    if base in path.resolve().parents and resolved != base and base not in resolved.parents:
                        errors.append(
                            f"{where}: link leaves overlay/{layout}/ and will break after install: {target}"
                        )

    if errors:
        print("FAILED")
        for error in errors:
            print(f"  - {error}")
        return 1
    largest = max(path.stat().st_size for path in OVERLAY.rglob("*.md"))
    counts = ", ".join(f"{len(spec['required'])} in overlay/{layout}" for layout, spec in LAYOUTS.items())
    print(
        f"OK: required files present ({counts}); front matter and links valid; "
        f"largest file {largest} of {MAX_OVERLAY_FILE_BYTES} bytes"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
