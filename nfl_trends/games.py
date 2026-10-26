"""Load nflverse games from edge-library data/. Never read Twin's nfl-ai tree."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

# nfl-ai main commit SHA for the copied data/games.csv (GitHub contents API).
NFL_AI_DATA_SHA = "ea0ce2810fc9f10f7cc7e3f3912807316102f218"
NFL_AI_DATA_COMMITTED_AT = "2026-10-26T05:09:03Z"

MINIMUM_SEASON = 2020
SITUATIONAL_MINIMUM_SEASON = 2010


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def default_games_path(root: Path | str | None = None) -> Path:
    base = Path(root) if root is not None else repo_root()
    return base / "data" / "games.csv"


def assert_unique(frame: pd.DataFrame, columns: list[str], label: str) -> None:
    duplicate_count = int(frame.duplicated(columns, keep=False).sum())
    if duplicate_count:
        joined = ", ".join(columns)
        raise ValueError(
            f"{label} contains {duplicate_count} duplicate rows for key: {joined}"
        )


def latest_season_split(
    frame: pd.DataFrame, season_column: str = "season"
) -> tuple[pd.DataFrame, pd.DataFrame, int]:
    if frame.empty:
        raise ValueError("Cannot split an empty dataset")
    holdout_season = int(frame[season_column].max())
    development = frame.loc[frame[season_column] < holdout_season].copy()
    holdout = frame.loc[frame[season_column] == holdout_season].copy()
    return development, holdout, holdout_season


def _require_columns(frame: pd.DataFrame, required: set[str], source: Path) -> None:
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise ValueError(f"{source} missing required columns: {', '.join(missing)}")


def load_games(
    path: Path | str | None = None,
    minimum_season: int = MINIMUM_SEASON,
    *,
    require_scores: bool = True,
) -> pd.DataFrame:
    source = Path(path) if path is not None else default_games_path()
    if not source.is_absolute():
        source = repo_root() / source
    frame = pd.read_csv(source)
    _require_columns(
        frame,
        {
            "game_id",
            "season",
            "home_team",
            "away_team",
            "home_score",
            "away_score",
        },
        source,
    )

    frame = frame.copy()
    frame["season"] = pd.to_numeric(frame["season"], errors="raise").astype(int)
    frame = frame.loc[frame["season"].ge(minimum_season)]
    if require_scores:
        frame = frame.dropna(subset=["home_score", "away_score"]).copy()
    assert_unique(frame, ["game_id"], "games")

    for column in (
        "home_score",
        "away_score",
        "total_line",
        "spread_line",
        "temp",
        "wind",
        "home_rest",
        "away_rest",
    ):
        if column in frame:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")

    if "roof" in frame.columns:
        roof = frame["roof"].fillna("unknown").astype(str).str.lower()
        frame["environment"] = roof.map(
            {
                "dome": "indoor",
                "closed": "indoor",
                "outdoors": "outdoor",
                "open": "outdoor",
            }
        ).fillna("unknown")
    return frame.reset_index(drop=True)
