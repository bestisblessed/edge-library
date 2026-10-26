#!/usr/bin/env bash
# Refresh edge-library data/ from Twin's local nfl-ai checkout.
#
# Usage:
#   cd ~/Code/edge-library && ./update_data.sh
#   NFL_AI_DIR=/other/path/nfl-ai ./update_data.sh
#
# Copies the same master scraper outputs the nfl-ai website and models read:
#   Scrapers/data/            -> data/
#   Scrapers/final_data_pfr/  -> data/final_data_pfr/
# Then deletes bak/, __pycache__, zips, and similar junk if any slipped in.
# data/ is replaced each run so stale files cannot linger.

set -euo pipefail

NFL_AI_DIR="${NFL_AI_DIR:-$HOME/Code/nfl-ai}"

# Expand a leading ~ if someone passed NFL_AI_DIR='~/Code/nfl-ai'
case "$NFL_AI_DIR" in
  "~/"*) NFL_AI_DIR="$HOME/${NFL_AI_DIR#~/}" ;;
  "~") NFL_AI_DIR="$HOME" ;;
esac

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEST_DIR="$SCRIPT_DIR/data"
SRC_DATA="$NFL_AI_DIR/Scrapers/data"
SRC_PFR="$NFL_AI_DIR/Scrapers/final_data_pfr"

if [[ ! -d "$NFL_AI_DIR" ]]; then
  echo "error: nfl-ai directory not found: $NFL_AI_DIR" >&2
  echo "Set NFL_AI_DIR to your local checkout, e.g. NFL_AI_DIR=/path/to/nfl-ai ./update_data.sh" >&2
  exit 1
fi

if [[ ! -d "$SRC_DATA" ]]; then
  echo "error: missing scraper data directory: $SRC_DATA" >&2
  exit 1
fi

echo "Source: $NFL_AI_DIR"
echo "Dest:   $DEST_DIR"

# Full replace so files removed upstream do not stay in data/.
rm -rf "$DEST_DIR"
mkdir -p "$DEST_DIR"

echo "Copying Scrapers/data/ -> data/"
cp -R "$SRC_DATA"/. "$DEST_DIR"/

if [[ -d "$SRC_PFR" ]]; then
  echo "Copying Scrapers/final_data_pfr/ -> data/final_data_pfr/"
  mkdir -p "$DEST_DIR/final_data_pfr"
  cp -R "$SRC_PFR"/. "$DEST_DIR/final_data_pfr"/
else
  echo "warning: $SRC_PFR not found; skipped PFR finals" >&2
fi

# Drop junk the scrapers sometimes leave beside the masters.
find "$DEST_DIR" \( -name bak -o -name __pycache__ \) -type d -prune -exec rm -rf {} + 2>/dev/null || true
find "$DEST_DIR" \( -name '*.zip' -o -name '*.pyc' -o -name .DS_Store \) -type f -delete 2>/dev/null || true

copied=()
while IFS= read -r name; do
  copied+=("$name")
done < <(ls -1 "$DEST_DIR")

echo
echo "Copied ${#copied[@]} top-level items into data/:"
for name in "${copied[@]}"; do
  if [[ -d "$DEST_DIR/$name" ]]; then
    echo "  $name/"
  else
    echo "  $name"
  fi
done

sha=""
if git -C "$NFL_AI_DIR" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  sha="$(git -C "$NFL_AI_DIR" rev-parse --short HEAD 2>/dev/null || true)"
fi
if [[ -n "$sha" ]]; then
  echo "nfl-ai HEAD: $sha"
else
  echo "nfl-ai HEAD: (not a git repo)"
fi
