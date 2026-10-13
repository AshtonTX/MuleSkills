#!/usr/bin/env bash
# Copy the guardrail files into a Mule project.
#
#   scripts/install.sh <path-to-mule-project> [--update]
#
# New files are copied. Existing files are never deleted. A file that already
# exists and differs is left alone and listed so you can merge it by hand.
# --update replaces the shared rule files (instructions, skill, recipes) with
# this repository's versions. It never replaces .github/copilot-instructions.md
# or .github/mule/team-profile.md, because those hold project-specific content.
set -euo pipefail

usage() { echo "Usage: $0 <path-to-mule-project> [--update]" >&2; exit 2; }
fail() { echo "Error: $*" >&2; exit 1; }
[ $# -ge 1 ] || usage
TARGET="$1"; shift
UPDATE=no
for arg in "$@"; do
  case "$arg" in
    --update) UPDATE=yes ;;
    *) usage ;;
  esac
done

SRC="$(cd -- "$(dirname "$0")/.." && pwd -P)/overlay"
[ ! -L "$SRC" ] && [ -d "$SRC/.github" ] || fail "Missing or unsafe overlay: $SRC"
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
      .github/copilot-instructions.md|.github/mule/team-profile.md) protected=yes ;;
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
  echo "Kept the project's own version of these (merge in anything new from overlay/ by hand):$kept"
fi
if [ -n "$merge" ]; then
  echo "These differ from this repository's version and were left alone. Run again with --update to replace them, or merge by hand:$merge"
fi
echo
echo "Next: fill in .github/mule/team-profile.md for this project, review the changes with git diff, and open a pull request."
