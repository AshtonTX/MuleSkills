#!/usr/bin/env bash
# Copy the guardrail files into a Mule project.
#
#   scripts/install.sh <path-to-mule-project> [--update] [--layout shared|github]
#
# --layout shared (the default) installs CLAUDE.md, .claude/rules, .claude/skills
# and .github/mule. Claude Code, GitHub Copilot CLI 1.0.89 or later and the
# GitHub Copilot desktop app all read those locations.
# --layout github installs the same rules as .github/copilot-instructions.md,
# .github/instructions and .github/skills, for Copilot clients that do not read
# .claude/rules. Claude Code reads none of those.
# Install one layout per project: Copilot loads both when both are present.
#
# New files are copied. Existing files are never deleted. A file that already
# exists and differs is left alone and listed so you can merge it by hand.
# --update replaces the shared rule files (rules, skill, recipes) with this
# repository's versions. It never replaces the repository-wide rules file
# (CLAUDE.md or .github/copilot-instructions.md) or .github/mule/team-profile.md,
# because those hold project-specific content.
set -euo pipefail

usage() { echo "Usage: $0 <path-to-mule-project> [--update] [--layout shared|github]" >&2; exit 2; }
fail() { echo "Error: $*" >&2; exit 1; }
[ $# -ge 1 ] || usage
TARGET="$1"; shift
UPDATE=no
LAYOUT=shared
while [ $# -gt 0 ]; do
  case "$1" in
    --update) UPDATE=yes ;;
    --layout) [ $# -ge 2 ] || usage; LAYOUT="$2"; shift ;;
    --layout=*) LAYOUT="${1#--layout=}" ;;
    *) usage ;;
  esac
  shift
done
case "$LAYOUT" in
  shared) OTHER=github; OWN_RULES=CLAUDE.md; OTHER_RULES=.github/copilot-instructions.md ;;
  github) OTHER=shared; OWN_RULES=.github/copilot-instructions.md; OTHER_RULES=CLAUDE.md ;;
  *) usage ;;
esac

BASE="$(cd -- "$(dirname "$0")/.." && pwd -P)/overlay"
SRC="$BASE/$LAYOUT"
OTHER_SRC="$BASE/$OTHER"
[ ! -L "$BASE" ] && [ ! -L "$SRC" ] && [ -d "$SRC" ] || fail "Missing or unsafe overlay: $SRC"
[ -d "$TARGET" ] || fail "Not a folder: $TARGET"
TARGET="$(cd -- "$TARGET" && pwd -P)"
[ -f "$TARGET/pom.xml" ] || echo "Warning: no pom.xml in $TARGET. Is this the Mule project root?"

# Inspect the complete copy operation before creating or replacing any files.
# A linked parent directory can redirect even a new file outside the project.
check_destination() {
  local rel="$1" parent="$TARGET" rest="$1" dest
  while [[ "$rest" = */* ]]; do
    parent="${parent%/}/${rest%%/*}"
    [ ! -L "$parent" ] || fail "Destination contains a symbolic link: $parent"
    if [ -e "$parent" ] && [ ! -d "$parent" ]; then
      fail "Destination parent is not a directory: $parent"
    fi
    rest="${rest#*/}"
  done
  dest="${TARGET%/}/$rel"
  [ ! -L "$dest" ] || fail "Destination is a symbolic link: $dest"
  if [ -e "$dest" ] && [ ! -f "$dest" ]; then
    fail "Destination is not a regular file: $dest"
  fi
}

# Capture find's status directly; failures inside process substitution do not
# propagate to the surrounding loop. NUL delimiters also preserve file names.
manifest="$(mktemp "${TMPDIR:-/tmp}/mule-guardrails.XXXXXX")"
trap 'rm -f "$manifest"' EXIT
trap 'exit 1' HUP INT TERM
find "$SRC" -print0 > "$manifest" || fail "Could not enumerate overlay: $SRC"
files=()
file_count=0
while IFS= read -r -d '' file; do
  [ ! -L "$file" ] || fail "Overlay contains a symbolic link: $file"
  [ ! -d "$file" ] || continue
  [ -f "$file" ] || fail "Overlay contains a non-regular file: $file"
  [ "${file##*/}" != '.DS_Store' ] || continue
  [ -r "$file" ] || fail "Overlay file is not readable: $file"
  rel="${file#"$SRC"/}"
  check_destination "$rel"
  files+=("$file")
  file_count=$((file_count + 1))
done < "$manifest"
[ "$file_count" -gt 0 ] || fail "Overlay contains no files: $SRC"

# Refuse to add this layout beside the other one. Copilot reads both sets of
# rule files, so every rule would be loaded twice. Files the two layouts share
# (.github/mule) are not a conflict, and the other layout's repository-wide
# rules file may be the project's own, so it only earns a note.
conflicts=""; note=""
if [ -d "$OTHER_SRC" ] && [ ! -L "$OTHER_SRC" ]; then
  find "$OTHER_SRC" -type f -print0 > "$manifest" || fail "Could not enumerate overlay: $OTHER_SRC"
  while IFS= read -r -d '' file; do
    rel="${file#"$OTHER_SRC"/}"
    [ "${file##*/}" != '.DS_Store' ] || continue
    [ ! -e "$SRC/$rel" ] || continue
    [ -e "${TARGET%/}/$rel" ] || [ -L "${TARGET%/}/$rel" ] || continue
    if [ "$rel" = "$OTHER_RULES" ]; then
      note="$rel"
    else
      conflicts="$conflicts
  $rel"
    fi
  done < "$manifest"
fi
if [ -n "$conflicts" ]; then
  echo "Error: this project already has rule files from the '$OTHER' layout:$conflicts" >&2
  echo "Installing the '$LAYOUT' layout beside them would make Copilot load every rule twice." >&2
  echo "Either keep that layout (run again with --layout $OTHER), or delete those files and run again." >&2
  exit 1
fi

added=0; same=0; updated=0; merge=""; kept=""
for file in "${files[@]}"; do
  rel="${file#"$SRC"/}"
  dest="${TARGET%/}/$rel"
  if [ ! -e "$dest" ]; then
    mkdir -p "${dest%/*}"
    cp "$file" "$dest"
    echo "  added    $rel"; added=$((added + 1))
  elif cmp -s "$file" "$dest"; then
    same=$((same + 1))
  else
    case "$rel" in
      "$OWN_RULES"|.github/mule/team-profile.md) protected=yes ;;
      *) protected=no ;;
    esac
    if [ "$protected" = yes ]; then
      kept="$kept
  $rel"
    elif [ "$UPDATE" = yes ]; then
      cp "$file" "$dest"
      echo "  updated  $rel"; updated=$((updated + 1))
    else
      merge="$merge
  $rel"
    fi
  fi
done

echo
echo "Added $added, updated $updated, already current $same."
if [ -n "$kept" ]; then
  echo "Kept the project's own version of these (merge in anything new from overlay/$LAYOUT/ by hand):$kept"
fi
if [ -n "$merge" ]; then
  echo "These differ from this repository's version and were left alone. Run again with --update to replace them, or merge by hand:$merge"
fi
if [ -n "$note" ]; then
  echo "Note: this project also has $note. Copilot loads it together with $OWN_RULES, so remove any guardrail text it still carries from an earlier install."
fi
echo
echo "Next: fill in .github/mule/team-profile.md for this project, review the changes with git diff, and open a pull request."
if [ "$LAYOUT" = shared ]; then
  echo "To see what loaded: run 'copilot instruction list' in the project (Copilot CLI 1.0.89 or later reads .claude/rules), or /memory in Claude Code."
fi
