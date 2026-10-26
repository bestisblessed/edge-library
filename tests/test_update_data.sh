#!/usr/bin/env bash
# Light fixture test for ./update_data.sh (no real nfl-ai required).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCRIPT="$ROOT/update_data.sh"
TMP="$(mktemp -d "${TMPDIR:-/tmp}/update-data-test.XXXXXX")"
trap 'rm -rf "$TMP"' EXIT

# Isolated copy so the test never touches the real data/ tree.
cp "$SCRIPT" "$TMP/update_data.sh"
chmod +x "$TMP/update_data.sh"

FAKE="$TMP/nfl-ai"
mkdir -p "$FAKE/Scrapers/data/rosters"
mkdir -p "$FAKE/Scrapers/data/bak"
mkdir -p "$FAKE/Scrapers/data/__pycache__"
mkdir -p "$FAKE/Scrapers/final_data_pfr"
printf 'game_id,home_team\n1,DET\n' > "$FAKE/Scrapers/data/games.csv"
printf 'player,team\nA,DET\n' > "$FAKE/Scrapers/data/rosters/roster_2026.csv"
printf 'old\n' > "$FAKE/Scrapers/data/bak/stale.csv"
printf 'x' > "$FAKE/Scrapers/data/__pycache__/junk.pyc"
printf 'zip' > "$FAKE/Scrapers/data/legacy.zip"
printf 'Game_ID,Detail\n1,TD\n' > "$FAKE/Scrapers/final_data_pfr/scoring_tables_pfr.csv"
git -C "$FAKE" init -q
git -C "$FAKE" config user.email "test@example.com"
git -C "$FAKE" config user.name "test"
git -C "$FAKE" add Scrapers
git -C "$FAKE" commit -q -m "fixture"
# Leave a stale dest file that must disappear after the replace.
mkdir -p "$TMP/data"
printf 'stale\n' > "$TMP/data/stale_leftover.csv"

fail_missing="$(NFL_AI_DIR="$TMP/does-not-exist" "$TMP/update_data.sh" 2>&1 || true)"
echo "$fail_missing" | grep -q "not found" || {
  echo "expected a missing-path error" >&2
  exit 1
}

out="$(NFL_AI_DIR="$FAKE" "$TMP/update_data.sh")"
echo "$out"

[[ -f "$TMP/data/games.csv" ]] || { echo "missing games.csv" >&2; exit 1; }
[[ -f "$TMP/data/rosters/roster_2026.csv" ]] || { echo "missing roster" >&2; exit 1; }
[[ -f "$TMP/data/final_data_pfr/scoring_tables_pfr.csv" ]] || { echo "missing pfr scoring" >&2; exit 1; }
[[ ! -e "$TMP/data/stale_leftover.csv" ]] || { echo "stale dest file survived" >&2; exit 1; }
[[ ! -e "$TMP/data/bak" ]] || { echo "bak/ was copied" >&2; exit 1; }
[[ ! -e "$TMP/data/__pycache__" ]] || { echo "__pycache__/ was copied" >&2; exit 1; }
[[ ! -e "$TMP/data/legacy.zip" ]] || { echo "zip was copied" >&2; exit 1; }
echo "$out" | grep -q "nfl-ai HEAD:" || { echo "missing SHA line" >&2; exit 1; }

echo "ok"
