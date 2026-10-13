#!/usr/bin/env python3
"""Generate overlay/github from overlay/shared.

overlay/shared is the hand-edited source and the default installation. It uses
the locations that Claude Code, GitHub Copilot CLI (1.0.89 or later) and the
GitHub Copilot desktop app all read: CLAUDE.md, .claude/rules, .claude/skills,
plus .github/mule for the team profile and recipes.

overlay/github holds the same content in GitHub Copilot's own locations
(.github/copilot-instructions.md, .github/instructions, .github/skills), for
clients that do not read .claude/rules. It is generated. Edit overlay/shared,
then run this script.

  python3 scripts/build.py           rewrite overlay/github
  python3 scripts/build.py --check   exit 1 if overlay/github is out of date

Only three things differ between the layouts: where each file lives, the
front-matter key that scopes a rule (`paths` or `applyTo`), and the relative
links between files, which are recomputed for the new locations.

Uses only the Python standard library (3.9 or later).
"""
import posixpath
import re
import sys
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parent.parent
SHARED = ROOT / "overlay/shared"
GITHUB = ROOT / "overlay/github"

# Every inline link form scripts/check.py recognizes: a bare or <angle-bracketed>
# destination, optionally followed by a title. convert() rewrites the bare form,
# with or without a title, and refuses a relative destination in any other form,
# so no link is ever copied into the other layout unconverted.
LINK = re.compile(
    r"(?P<open>\[[^\]\n]*\]\()"
    r"(?:<(?P<angle>[^<>\n]+)>|(?P<bare>(?:\\.|[^\s()\\]|\([^()\n]*\))+))"
    r"(?P<title>\s+(?:\"(?:\\.|[^\"\\])*\"|'(?:\\.|[^'\\])*'|\([^()]*\)))?"
    r"(?P<close>\s*\))"
)
# A reference-style definition: [label]: destination "optional title". Markdown
# allows one line break between the colon and the destination.
# Footnote definitions ([^note]: text) are not links and are left alone.
REFERENCE = re.compile(
    r"^(?P<open>[ ]{0,3}\[(?!\^)[^\]\n]+\]:[ \t]*(?:\n[ \t]*)?)"
    r"(?:<(?P<angle>[^<>\n]+)>|(?P<bare>\S+))"
    r"(?P<close>[^\n]*)$",
    re.M,
)
SCHEME = re.compile(r"^[a-z][a-z0-9+.-]*:", re.I)
# Raw HTML can link too. It is not converted, so a relative target is refused.
HTML_LINK = re.compile(r"""\b(?:href|src)\s*=\s*(["'])(?P<destination>[^"'\n]*)\1""", re.I)
# Every file that moves lives under one of these names in the shared layout. If
# one still appears in a generated file, some path was written in a form that
# convert() does not recognize (plain text, a code span, an unusual link).
SHARED_ONLY = re.compile(r"\.claude/|CLAUDE\.md")


def to_github(rel):
    """Map a path in the shared layout to its place in the GitHub layout."""
    parts = PurePosixPath(rel).parts
    if parts == ("CLAUDE.md",):
        return PurePosixPath(".github/copilot-instructions.md")
    if parts[:2] == (".claude", "rules"):
        rest = parts[2:]
        if rest and rest[-1].endswith(".md"):
            rest = rest[:-1] + (rest[-1][: -len(".md")] + ".instructions.md",)
        return PurePosixPath(".github", "instructions", *rest)
    if parts[:2] == (".claude", "skills"):
        return PurePosixPath(".github", "skills", *parts[2:])
    if parts[:2] == (".github", "mule"):
        return PurePosixPath(*parts)
    raise ValueError(f"{rel}: no place for this path in the GitHub layout")


def to_shared(rel):
    """The inverse of to_github, used to bring GitHub-layout content back."""
    parts = PurePosixPath(rel).parts
    if parts == (".github", "copilot-instructions.md"):
        return PurePosixPath("CLAUDE.md")
    if parts[:2] == (".github", "instructions"):
        rest = parts[2:]
        if rest and rest[-1].endswith(".instructions.md"):
            rest = rest[:-1] + (rest[-1][: -len(".instructions.md")] + ".md",)
        return PurePosixPath(".claude", "rules", *rest)
    if parts[:2] == (".github", "skills"):
        return PurePosixPath(".claude", "skills", *parts[2:])
    if parts[:2] == (".github", "mule"):
        return PurePosixPath(*parts)
    raise ValueError(f"{rel}: no place for this path in the shared layout")


def is_rule(rel, rules_dir):
    return PurePosixPath(rel).parts[: len(rules_dir)] == rules_dir and str(rel).endswith(".md")


def rename_scope_key(text, old, new):
    """Rename the front-matter key that scopes a rule file, leaving its value alone."""
    if not re.match(r"---\r?\n", text):
        raise ValueError("rule file has no front matter")
    end = text.find("\n---", 3)
    if end < 0:
        raise ValueError("rule file front matter is not closed")
    head, rest = text[:end], text[end:]
    pattern = re.compile(rf"^{re.escape(old)}:", re.M)
    if len(pattern.findall(head)) != 1:
        raise ValueError(f"rule file front matter must set {old} exactly once")
    return pattern.sub(f"{new}:", head) + rest


def convert(text, source, target, mapping, exists):
    """Recompute every relative link in `text` for the file's new location.

    Covers inline links and reference-style definitions, so no relative
    destination is copied into the other layout unconverted.
    """

    def rewrite(match):
        destination = match.group("angle") or match.group("bare")
        if SCHEME.match(destination) or destination.startswith("#"):
            return match.group(0)
        path, hash_mark, fragment = destination.partition("#")
        if match.group("angle") or not path or re.search(r"[\\%?()]", path):
            raise ValueError(
                f"{source}: cannot convert link {destination}; write it as a plain relative path, "
                "without angle brackets, escapes, parentheses or a query"
            )
        resolved = posixpath.normpath(posixpath.join(posixpath.dirname(str(source)), path))
        if resolved.startswith("..") or not exists(resolved):
            raise ValueError(f"{source}: link {destination} does not point inside the layout")
        moved = posixpath.relpath(str(mapping(resolved)), posixpath.dirname(str(target)) or ".")
        if path.endswith("/"):
            moved += "/"
        title = match.groupdict().get("title") or ""
        return match.group("open") + moved + hash_mark + fragment + title + match.group("close")

    for match in HTML_LINK.finditer(text):
        destination = match.group("destination")
        if not (SCHEME.match(destination) or destination.startswith("#")):
            raise ValueError(f"{source}: cannot convert HTML link {destination}; use a Markdown link")
    return REFERENCE.sub(rewrite, LINK.sub(rewrite, text))


def convert_tree(source_root, mapping, old_key, new_key, rules_dir):
    """Return {relative path: bytes} for every file of `source_root` in the other layout."""
    result = {}
    files = sorted(p for p in source_root.rglob("*") if p.is_file() and p.name != ".DS_Store")
    if not files:
        raise ValueError(f"{source_root}: no files to convert")
    for path in files:
        if path.is_symlink():
            raise ValueError(f"{path}: symbolic links are not supported in the overlay")
        source = PurePosixPath(path.relative_to(source_root).as_posix())
        target = mapping(source)
        data = path.read_bytes()
        if path.suffix == ".md":
            text = data.decode("utf-8")
            if is_rule(source, rules_dir):
                text = rename_scope_key(text, old_key, new_key)
            text = convert(text, source, target, mapping, lambda rel: (source_root / rel).exists())
            data = text.encode("utf-8")
        if str(target) in result:
            raise ValueError(f"{source}: two files map to {target}")
        result[str(target)] = data
    return result


def build_github():
    result = convert_tree(SHARED, to_github, "paths", "applyTo", (".claude", "rules"))
    for name, data in result.items():
        leftover = SHARED_ONLY.search(data.decode("utf-8")) if name.endswith(".md") else None
        if leftover:
            raise ValueError(
                f"overlay/github/{name} would still mention {leftover.group(0)}, which does not exist in that layout; "
                "in overlay/shared, write the path as a Markdown link so it can be converted"
            )
    return result


def current(root):
    if not root.is_dir():
        return {}
    return {
        p.relative_to(root).as_posix(): p.read_bytes()
        for p in sorted(root.rglob("*"))
        if p.is_file() and p.name != ".DS_Store"
    }


def main(argv):
    if argv not in ([], ["--check"]):
        print(__doc__.strip().splitlines()[0], file=sys.stderr)
        print("Usage: build.py [--check]", file=sys.stderr)
        return 2
    try:
        wanted = build_github()
    except (OSError, ValueError) as error:
        print(f"FAILED: {error}")
        return 1
    existing = current(GITHUB)
    stale = sorted(k for k in wanted if existing.get(k) != wanted[k])
    extra = sorted(k for k in existing if k not in wanted)
    if argv == ["--check"]:
        if stale or extra:
            print("FAILED: overlay/github is out of date; run python3 scripts/build.py")
            for name in stale:
                print(f"  - differs or missing: overlay/github/{name}")
            for name in extra:
                print(f"  - no longer generated: overlay/github/{name}")
            return 1
        print(f"OK: overlay/github matches overlay/shared ({len(wanted)} files)")
        return 0
    for name in extra:
        (GITHUB / name).unlink()
    for name in stale:
        path = GITHUB / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(wanted[name])
    for directory in sorted((p for p in GITHUB.rglob("*") if p.is_dir()), reverse=True):
        if not any(directory.iterdir()):
            directory.rmdir()
    print(f"Wrote overlay/github: {len(stale)} updated, {len(extra)} removed, {len(wanted) - len(stale)} unchanged")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
