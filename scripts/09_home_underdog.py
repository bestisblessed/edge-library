#!/usr/bin/env python3
"""Team as a home underdog.

Reproduces the KillerSports/SBBreakers claim that the Eagles have not won as a
home dog since the 2020 season (published 0-9 SU, 2-7 ATS).

``spread_line`` is nflverse expected home scoring margin. A home dog is
``spread_line < 0``. Pick'em (``spread_line == 0``) is excluded. Pushes are
graded, not dropped.

"Since the 2020 season" is ambiguous. This module tests:

- NFL season 2020 inclusive
- NFL season 2021 onward
- Calendar start date 2021-01-01 (includes 2020 week 17, played 3 Jan 2021)

The calendar cut is the reading that matches 0-9 SU / 2-7 ATS on repository
closing lines, so it is the default ``--start-date``.

Reads only ``data/games.csv`` (repo-root relative). Run from the repository root:

    python scripts/09_home_underdog.py
    python scripts/09_home_underdog.py --notebook
"""

# Source: @SBBreakers, 2026-10-26 — https://x.com/SBBreakers/status/2114782848607805951

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass, field
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

@dataclass
class EdgeResult:
    id: str
    summary: pd.DataFrame
    audit: pd.DataFrame
    secondary: dict[str, pd.DataFrame] = field(default_factory=dict)
    metadata: dict = field(default_factory=dict)

WIN_RETURN_AT_MINUS_110 = 100 / 110


def grade_totals(games: pd.DataFrame) -> pd.DataFrame:
    result = games.copy()
    result["actual_total"] = result["home_score"] + result["away_score"]
    result["total_margin"] = result["actual_total"] - result["total_line"]
    result["total_result"] = np.select(
        [result["total_margin"] > 0, result["total_margin"] < 0],
        ["over", "under"],
        default="push",
    )
    return result


def grade_home_spread(games: pd.DataFrame) -> pd.DataFrame:
    result = games.copy()
    result["home_margin"] = result["home_score"] - result["away_score"]
    result["home_ats_margin"] = result["home_margin"] - result["spread_line"]
    result["home_ats_result"] = np.select(
        [result["home_ats_margin"] > 0, result["home_ats_margin"] < 0],
        ["cover", "no_cover"],
        default="push",
    )
    return result


def flat_bet_profit(results: pd.Series, win_label: str) -> pd.Series:
    return pd.Series(
        np.select(
            [results.eq(win_label), results.eq("push")],
            [WIN_RETURN_AT_MINUS_110, 0.0],
            default=-1.0,
        ),
        index=results.index,
        dtype=float,
    )


def wilson_interval(
    wins: int, trials: int, z: float = 1.959963984540054
) -> tuple[float, float]:
    if trials <= 0:
        return (math.nan, math.nan)
    rate = wins / trials
    denominator = 1 + (z**2 / trials)
    center = (rate + z**2 / (2 * trials)) / denominator
    margin = (
        z
        * math.sqrt((rate * (1 - rate) / trials) + (z**2 / (4 * trials**2)))
        / denominator
    )
    return max(0.0, center - margin), min(1.0, center + margin)


def summarize_binary_market(
    results: pd.Series, win_label: str
) -> dict[str, float | int]:
    observed = results.dropna()
    games = int(len(observed))
    pushes = int(observed.eq("push").sum())
    decisions = games - pushes
    wins = int(observed.eq(win_label).sum())
    low, high = wilson_interval(wins, decisions)
    profits = flat_bet_profit(observed, win_label=win_label)
    return {
        "games": games,
        "decisions": decisions,
        "wins": wins,
        "pushes": pushes,
        "win_rate": wins / decisions if decisions else math.nan,
        "ci_low": low,
        "ci_high": high,
        "roi_units": float(profits.sum() / games) if games else math.nan,
    }

# Twin's committed data/ snapshot on edge-library main (d0f3074 "Refresh NFL data").
DATA_SNAPSHOT_SHA = "d0f3074ac22eff9b45ab42329c51cbda227bff0a"
DATA_SNAPSHOT_COMMITTED_AT = "2026-10-26T16:18:57-04:00"

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

def metadata_for(frame: pd.DataFrame, source_rows: int) -> dict:
    development, holdout, holdout_season = latest_season_split(frame)
    return {
        "source_rows": int(source_rows),
        "included_rows": int(len(frame)),
        "excluded_rows": int(source_rows - len(frame)),
        "season_start": int(frame["season"].min()),
        "season_end": int(frame["season"].max()),
        "development_rows": int(len(development)),
        "holdout_season": holdout_season,
        "holdout_rows": int(len(holdout)),
    }


def split_research_frame(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return development rows and the latest-season temporal holdout."""
    development, holdout, _ = latest_season_split(frame)
    return development.copy(), holdout.copy()


def market_summary(
    frame: pd.DataFrame,
    group_columns: list[str],
    result_column: str,
    win_label: str,
    value_columns: tuple[str, ...] = (),
) -> pd.DataFrame:
    rows = []
    grouper = group_columns[0] if len(group_columns) == 1 else group_columns
    for key, group in frame.groupby(grouper, observed=True, dropna=False):
        keys = (key,) if len(group_columns) == 1 else key
        row = dict(zip(group_columns, keys))
        row.update(summarize_binary_market(group[result_column], win_label=win_label))
        for column in value_columns:
            row[f"avg_{column}"] = float(group[column].mean())
        rows.append(row)
    return pd.DataFrame(rows)


def descriptive_summary(
    frame: pd.DataFrame, group_columns: list[str], value_columns: tuple[str, ...]
) -> pd.DataFrame:
    rows = []
    grouper = group_columns[0] if len(group_columns) == 1 else group_columns
    for key, group in frame.groupby(grouper, observed=True, dropna=False):
        keys = (key,) if len(group_columns) == 1 else key
        row = dict(zip(group_columns, keys))
        row["games"] = int(len(group))
        for column in value_columns:
            row[f"avg_{column}"] = float(group[column].mean())
        rows.append(row)
    return pd.DataFrame(rows)


def safe_ratio(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator else math.nan

DIVISIONS = {
    "AFC East": ["BUF", "MIA", "NE", "NYJ"],
    "AFC North": ["BAL", "CIN", "CLE", "PIT"],
    "AFC South": ["HOU", "IND", "JAX", "TEN"],
    "AFC West": ["DEN", "KC", "LAC", "LVR"],
    "NFC East": ["DAL", "NYG", "PHI", "WAS"],
    "NFC North": ["CHI", "DET", "GB", "MIN"],
    "NFC South": ["ATL", "CAR", "NO", "TB"],
    "NFC West": ["ARI", "LAR", "SF", "SEA"],
}
TEAM_TO_DIVISION = {
    team: division for division, teams in DIVISIONS.items() for team in teams
}

BLUE = "#1f4e79"
GOLD = "#c69214"
INK = "#252525"
GRID = "#d9dde3"
OVER = "#2e7d32"
UNDER = "#c62828"
COVER = "#2e7d32"
NO_COVER = "#c62828"
PUSH = "#6b7280"
LIVE = "#7b1fa2"


def _style(axis) -> None:
    axis.spines[["top", "right"]].set_visible(False)
    axis.grid(axis="y", color=GRID, linewidth=0.8, alpha=0.8)
    axis.set_axisbelow(True)
    axis.tick_params(axis="x", labelrotation=25)


def _rested_after_scoring_chart(result: EdgeResult) -> Figure:
    games = result.audit.loc[result.audit["qualifies"]].copy()
    games = games.sort_values(["date", "game_id"]).reset_index(drop=True)
    figure, axis = plt.subplots(figsize=(12, 6))
    if games.empty:
        axis.set_title("No qualifying games")
        axis.set_xlabel("Game")
        axis.set_ylabel("Points")
        _style(axis)
        figure.tight_layout()
        return figure

    labels = []
    for row in games.itertuples(index=False):
        date_value = pd.Timestamp(row.date).strftime("%Y-%m-%d")
        side = "vs" if bool(row.is_home) else "@"
        suffix = " LIVE" if bool(row.is_live) else ""
        labels.append(f"{date_value}\n{side} {row.opponent}{suffix}")
    x = np.arange(len(games))
    result_colors = {"over": OVER, "under": UNDER, "push": PUSH}

    for index, row in games.iterrows():
        total_line = row["total_line"]
        actual = row["actual_total"]
        if pd.notna(total_line) and pd.notna(actual):
            axis.plot(
                [index, index],
                [total_line, actual],
                color=GRID,
                linewidth=1.6,
                zorder=1,
            )
            axis.scatter(
                [index],
                [actual],
                color=result_colors.get(row["total_result"], INK),
                s=70,
                zorder=3,
                edgecolors="white",
                linewidths=0.6,
            )
            axis.scatter(
                [index],
                [total_line],
                color=GOLD,
                marker="s",
                s=36,
                zorder=2,
            )
        elif pd.notna(total_line):
            axis.scatter(
                [index],
                [total_line],
                color=LIVE,
                marker="D",
                s=70,
                zorder=3,
                facecolors="white",
                edgecolors=LIVE,
                linewidths=1.6,
            )

    overs = int(result.metadata.get("claimed_overs", 0))
    unders = int(result.metadata.get("claimed_unders", 0))
    pushes = int(result.metadata.get("claimed_pushes", 0))
    team = result.metadata.get("team", "")
    axis.scatter([], [], color=OVER, s=70, label="Combined points (over)")
    axis.scatter([], [], color=UNDER, s=70, label="Combined points (under)")
    axis.scatter([], [], color=GOLD, marker="s", s=36, label="Closing total")
    axis.scatter(
        [],
        [],
        color=LIVE,
        marker="D",
        s=70,
        facecolors="white",
        edgecolors=LIVE,
        label="Live qualifier (unscored)",
    )
    axis.set_xticks(x, labels)
    axis.set_xlabel("Qualifying game")
    axis.set_ylabel("Points")
    axis.set_title(
        f"{team} extra rest after 24+ previous game: {overs}-{unders}-{pushes} to the over"
    )
    axis.set_ylim(bottom=0)
    axis.legend(frameon=False, loc="upper left")
    _style(axis)
    axis.tick_params(axis="x", labelrotation=0, labelsize=7)
    figure.tight_layout()
    return figure


def _qualifying_ats_margin_chart(result: EdgeResult) -> Figure:
    games = result.audit.loc[result.audit["qualifies"]].copy()
    games = games.sort_values(["date", "game_id"]).reset_index(drop=True)
    figure, axis = plt.subplots(figsize=(12, 6))
    team = result.metadata.get("team", "")
    su = (
        f"{result.metadata.get('claimed_su_wins', 0)}-"
        f"{result.metadata.get('claimed_su_losses', 0)}"
    )
    ats = (
        f"{result.metadata.get('claimed_ats_wins', 0)}-"
        f"{result.metadata.get('claimed_ats_losses', 0)}"
    )
    title = f"{team}: {su} SU, {ats} ATS"
    if games.empty:
        axis.set_title(title)
        axis.set_xlabel("Qualifying game")
        axis.set_ylabel("ATS margin (team)")
        _style(axis)
        figure.tight_layout()
        return figure

    labels = []
    for row in games.itertuples(index=False):
        date_value = pd.Timestamp(row.date).strftime("%Y-%m-%d")
        side = "vs" if bool(row.is_home) else "@"
        suffix = " LIVE" if bool(row.is_live) else ""
        labels.append(f"{date_value}\n{side} {row.opponent}{suffix}")
    x = np.arange(len(games))
    colors = []
    heights = []
    for _, row in games.iterrows():
        if bool(row["is_live"]) or pd.isna(row["team_ats_margin"]):
            colors.append(LIVE)
            heights.append(0.0)
        elif row["ats_result"] == "cover":
            colors.append(COVER)
            heights.append(float(row["team_ats_margin"]))
        elif row["ats_result"] == "push":
            colors.append(PUSH)
            heights.append(float(row["team_ats_margin"]))
        else:
            colors.append(NO_COVER)
            heights.append(float(row["team_ats_margin"]))
    axis.bar(x, heights, color=colors, width=0.72, zorder=2)
    axis.axhline(0, color=INK, linewidth=1, zorder=1)
    axis.scatter(
        x[games["is_live"].fillna(False).to_numpy()],
        [0.0] * int(games["is_live"].fillna(False).sum()),
        color=LIVE,
        marker="D",
        s=70,
        zorder=3,
        facecolors="white",
        edgecolors=LIVE,
        linewidths=1.6,
    )
    axis.set_xticks(x, labels)
    axis.set_xlabel("Qualifying game")
    axis.set_ylabel("ATS margin (team)")
    axis.set_title(title)
    axis.legend(
        handles=[
            Patch(facecolor=COVER, label="ATS win"),
            Patch(facecolor=NO_COVER, label="ATS loss"),
            Patch(facecolor=PUSH, label="Push"),
            Line2D(
                [0],
                [0],
                marker="D",
                color="white",
                markerfacecolor="white",
                markeredgecolor=LIVE,
                markersize=8,
                linestyle="None",
                label="Live qualifier",
            ),
        ],
        frameon=False,
        loc="best",
    )
    _style(axis)
    axis.tick_params(axis="x", labelrotation=0, labelsize=7)
    figure.tight_layout()
    return figure


def chart_for_result(result: EdgeResult) -> Figure:
    if result.id == "rested-after-scoring-totals":
        return _rested_after_scoring_chart(result)
    if result.id in {"home-underdog", "division-underdog", "after-under"}:
        return _qualifying_ats_margin_chart(result)
    raise ValueError(f"No chart contract for edge: {result.id}")

PUBLIC_RESULT = {
    "win": "W",
    "loss": "L",
    "tie": "T",
    "cover": "W",
    "no_cover": "L",
    "push": "P",
}


def require_columns(frame: pd.DataFrame, columns: tuple[str, ...]) -> None:
    missing = [column for column in columns if column not in frame.columns]
    if missing:
        raise ValueError(f"games missing required columns: {', '.join(missing)}")


def parse_game_dates(frame: pd.DataFrame) -> pd.DataFrame:
    require_columns(frame, ("date",))
    out = frame.copy()
    out["date"] = pd.to_datetime(out["date"], errors="raise")
    return out


def apply_time_window(
    frame: pd.DataFrame,
    *,
    start_season: int | None = None,
    start_date: str | None = None,
    include_playoffs: bool = True,
) -> pd.DataFrame:
    out = frame
    if start_season is not None:
        out = out.loc[out["season"].ge(int(start_season))]
    if start_date is not None:
        out = out.loc[out["date"].ge(pd.Timestamp(start_date))]
    if not include_playoffs and "game_type" in out.columns:
        out = out.loc[out["game_type"].fillna("REG").eq("REG")]
    return out.copy()


def expand_team_games(games: pd.DataFrame) -> pd.DataFrame:
    """Stack home and away views and attach lagged team-game features.

    ``spread_line`` is nflverse expected home scoring margin: positive means the
    home team is favored, negative means the home team is the underdog, and 0 is
    pick'em. ``dog_points`` is that line from the row team's perspective
    (positive = underdog). Pick'em rows have ``dog_points == 0`` and are not
    dogs. Pushes are graded later as ``ats_result == "push"``.
    """
    require_columns(
        games,
        (
            "game_id",
            "season",
            "date",
            "home_team",
            "away_team",
            "home_score",
            "away_score",
            "spread_line",
        ),
    )
    frame = parse_game_dates(games)
    keep = [
        column
        for column in (
            "game_id",
            "season",
            "week",
            "game_type",
            "date",
            "weekday",
            "home_team",
            "away_team",
            "home_score",
            "away_score",
            "spread_line",
            "total_line",
            "location",
            "environment",
            "roof",
        )
        if column in frame.columns
    ]
    home = frame.loc[:, keep].assign(
        team=frame["home_team"],
        opponent=frame["away_team"],
        team_score=frame["home_score"],
        opponent_score=frame["away_score"],
        is_home=True,
    )
    away = frame.loc[:, keep].assign(
        team=frame["away_team"],
        opponent=frame["home_team"],
        team_score=frame["away_score"],
        opponent_score=frame["home_score"],
        is_home=False,
    )
    team_games = pd.concat([home, away], ignore_index=True)
    team_games = team_games.sort_values(["team", "date", "game_id"]).reset_index(
        drop=True
    )
    if "location" in team_games.columns:
        team_games["is_neutral"] = (
            team_games["location"].fillna("Home").str.lower().eq("neutral")
        )
    else:
        team_games["is_neutral"] = False
    team_games["home_away"] = np.where(team_games["is_home"], "vs", "@")
    team_games["dog_points"] = np.where(
        team_games["is_home"],
        -team_games["spread_line"],
        team_games["spread_line"],
    )
    team_games["is_dog"] = team_games["dog_points"].gt(0)
    team_games["is_pickem"] = team_games["spread_line"].eq(0)
    team_games["is_live"] = team_games["team_score"].isna() | team_games[
        "opponent_score"
    ].isna()
    team_games["team_margin"] = team_games["team_score"] - team_games["opponent_score"]
    team_games["team_ats_margin"] = np.where(
        team_games["is_home"],
        team_games["team_margin"] - team_games["spread_line"],
        team_games["team_margin"] + team_games["spread_line"],
    )
    team_games["actual_total"] = team_games["home_score"] + team_games["away_score"]
    if "total_line" in team_games.columns:
        team_games["total_margin"] = team_games["actual_total"] - team_games["total_line"]
        team_games["under_margin"] = -team_games["total_margin"]
    else:
        team_games["total_margin"] = np.nan
        team_games["under_margin"] = np.nan

    team_games["su_result"] = pd.Series(pd.NA, index=team_games.index, dtype=object)
    team_games["ats_result"] = pd.Series(pd.NA, index=team_games.index, dtype=object)
    scored = ~team_games["is_live"]
    team_games.loc[scored & team_games["team_margin"].gt(0), "su_result"] = "win"
    team_games.loc[scored & team_games["team_margin"].lt(0), "su_result"] = "loss"
    team_games.loc[scored & team_games["team_margin"].eq(0), "su_result"] = "tie"
    spread_ready = scored & team_games["spread_line"].notna() & team_games[
        "team_ats_margin"
    ].notna()
    team_games.loc[spread_ready & team_games["team_ats_margin"].gt(0), "ats_result"] = (
        "cover"
    )
    team_games.loc[spread_ready & team_games["team_ats_margin"].lt(0), "ats_result"] = (
        "no_cover"
    )
    team_games.loc[spread_ready & team_games["team_ats_margin"].eq(0), "ats_result"] = (
        "push"
    )

    grouped = team_games.groupby("team", sort=False)
    team_games["prior_team_score"] = grouped["team_score"].shift(1)
    team_games["prior_date"] = grouped["date"].shift(1)
    team_games["prior_season"] = grouped["season"].shift(1)
    team_games["prior_opponent"] = grouped["opponent"].shift(1)
    team_games["prior_actual_total"] = grouped["actual_total"].shift(1)
    team_games["prior_total_line"] = (
        grouped["total_line"].shift(1) if "total_line" in team_games.columns else np.nan
    )
    team_games["prior_total_margin"] = grouped["total_margin"].shift(1)
    team_games["prior_under_margin"] = grouped["under_margin"].shift(1)
    team_games["same_season_prior"] = team_games["prior_season"].eq(team_games["season"])
    team_games["team_division"] = team_games["team"].map(TEAM_TO_DIVISION)
    team_games["opponent_division"] = team_games["opponent"].map(TEAM_TO_DIVISION)
    team_games["is_divisional"] = team_games["team_division"].eq(
        team_games["opponent_division"]
    ) & team_games["team_division"].notna()
    return team_games


def filter_site(frame: pd.DataFrame, site: str) -> pd.DataFrame:
    if site == "both":
        return frame
    if site == "home":
        return frame.loc[frame["is_home"]].copy()
    if site == "road":
        return frame.loc[~frame["is_home"]].copy()
    raise ValueError(f"site must be home, road, or both; got {site!r}")


def public_result_label(value) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)) or pd.isna(value):
        return ""
    return PUBLIC_RESULT.get(str(value), str(value))


def format_score(team_score, opponent_score) -> str:
    if pd.isna(team_score) or pd.isna(opponent_score):
        return ""
    return f"{int(team_score)}-{int(opponent_score)}"


def qualifying_table(frame: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    table = frame.copy()
    if "qualifies" in table.columns:
        table = table.loc[table["qualifies"]].copy()
    table["final_score"] = [
        format_score(team_score, opponent_score)
        for team_score, opponent_score in zip(
            table.get("team_score", pd.Series(dtype=float)),
            table.get("opponent_score", pd.Series(dtype=float)),
        )
    ]
    if "su_result" in table.columns:
        table["su_result"] = table["su_result"].map(public_result_label)
    if "ats_result" in table.columns:
        table["ats_result"] = table["ats_result"].map(public_result_label)
    if "date" in table.columns:
        table["date"] = pd.to_datetime(table["date"]).dt.strftime("%Y-%m-%d")
    if "prior_date" in table.columns:
        table["prior_game_date"] = pd.to_datetime(
            table["prior_date"], errors="coerce"
        ).dt.strftime("%Y-%m-%d")
    table = table.rename(
        columns={
            "spread_line": "home_spread",
            "team_ats_margin": "margin_vs_spread",
            "team_margin": "win_margin",
            "prior_team_score": "prior_team_points",
            "prior_under_margin": "prior_under_margin",
            "prior_actual_total": "prior_combined_points",
        }
    )
    for column in columns:
        if column not in table.columns:
            table[column] = pd.NA
    sort_columns = [column for column in ("date", "game_id") if column in table.columns]
    table = table.loc[:, columns]
    if sort_columns:
        table = table.sort_values(sort_columns)
    return table.reset_index(drop=True)


def record_row(frame: pd.DataFrame, **dimensions) -> dict:
    graded_su = frame.loc[frame["su_result"].notna()]
    graded_ats = frame.loc[frame["ats_result"].notna()]
    su = summarize_binary_market(graded_su["su_result"], win_label="win")
    ats = summarize_binary_market(graded_ats["ats_result"], win_label="cover")
    row = dict(dimensions)
    row["games"] = int(len(graded_su))
    row["su_wins"] = int(su["wins"])
    row["su_losses"] = int((graded_su["su_result"] == "loss").sum())
    row["su_ties"] = int((graded_su["su_result"] == "tie").sum())
    row["ats_wins"] = int(ats["wins"])
    row["ats_losses"] = int((graded_ats["ats_result"] == "no_cover").sum())
    row["ats_pushes"] = int(ats["pushes"])
    row["ats_decisions"] = int(ats["decisions"])
    row["ats_win_rate"] = ats["win_rate"]
    row["ats_ci_low"] = ats["ci_low"]
    row["ats_ci_high"] = ats["ci_high"]
    row["ats_roi_units"] = ats["roi_units"]
    row["avg_win_margin"] = (
        float(graded_su["team_margin"].mean()) if len(graded_su) else float("nan")
    )
    row["avg_team_ats_margin"] = (
        float(graded_ats["team_ats_margin"].mean()) if len(graded_ats) else float("nan")
    )
    row["live_games"] = (
        int(frame["is_live"].fillna(False).sum()) if "is_live" in frame else 0
    )
    return row


def claimed_counts(frame: pd.DataFrame) -> dict[str, int]:
    graded = frame.loc[~frame["is_live"].fillna(False)]
    return {
        "claimed_su_wins": int((graded["su_result"] == "win").sum()),
        "claimed_su_losses": int((graded["su_result"] == "loss").sum()),
        "claimed_su_ties": int((graded["su_result"] == "tie").sum()),
        "claimed_ats_wins": int((graded["ats_result"] == "cover").sum()),
        "claimed_ats_losses": int((graded["ats_result"] == "no_cover").sum()),
        "claimed_ats_pushes": int((graded["ats_result"] == "push").sum()),
        "live_strategy_rows": int(frame["is_live"].fillna(False).sum()),
        "graded_strategy_rows": int(len(graded)),
        "strategy_rows": int(len(frame)),
    }


EDGE_ID = "home-underdog"
DEFAULT_TEAM = "PHI"
DEFAULT_START_DATE = "2021-01-01"
DEFAULT_MIN_SPREAD = 0.0
QUALIFYING_COLUMNS = [
    "date",
    "season",
    "week",
    "game_id",
    "opponent",
    "home_spread",
    "final_score",
    "su_result",
    "ats_result",
    "margin_vs_spread",
    "is_live",
]


def _qualifies(frame: pd.DataFrame, *, min_spread: float) -> pd.Series:
    return (
        frame["is_home"]
        & ~frame["is_neutral"].fillna(False)
        & frame["is_dog"].fillna(False)
        & frame["dog_points"].ge(min_spread)
        & frame["spread_line"].notna()
    )


def _window(
    team_games: pd.DataFrame,
    *,
    team: str | None,
    start_season: int | None,
    start_date: str | None,
    min_spread: float,
    include_playoffs: bool,
    home_only: bool,
) -> pd.DataFrame:
    window = apply_time_window(
        team_games,
        start_season=start_season,
        start_date=start_date,
        include_playoffs=include_playoffs,
    )
    if team is not None:
        window = window.loc[window["team"].eq(team)].copy()
    if home_only:
        window = window.loc[window["is_home"]].copy()
    window["qualifies"] = _qualifies(window, min_spread=min_spread)
    return window


def summaries(development_graded: pd.DataFrame, *, team: str) -> pd.DataFrame:
    summary = market_summary(
        development_graded,
        ["team"],
        "ats_result",
        "cover",
        ("team_margin", "team_ats_margin", "spread_line"),
    )
    if summary.empty:
        summary = pd.DataFrame([record_row(development_graded, team=team)])
    if "sample" not in summary.columns:
        summary.insert(1, "sample", "development")
    return summary


def analyze(
    games: pd.DataFrame,
    *,
    team: str = DEFAULT_TEAM,
    start_season: int | None = None,
    start_date: str | None = DEFAULT_START_DATE,
    min_spread: float = DEFAULT_MIN_SPREAD,
    include_playoffs: bool = True,
) -> EdgeResult:
    source_rows = len(games)
    team_games = expand_team_games(games)
    audit = _window(
        team_games,
        team=team,
        start_season=start_season,
        start_date=start_date,
        min_spread=min_spread,
        include_playoffs=include_playoffs,
        home_only=True,
    )
    if audit.empty:
        raise ValueError(f"No home games for {team} in the requested window")

    qualifiers = audit.loc[audit["qualifies"]].copy()
    graded = qualifiers.loc[qualifiers["ats_result"].notna()].copy()
    development, holdout = split_research_frame(audit)
    development_graded = development.loc[
        development["qualifies"] & development["ats_result"].notna()
    ]
    holdout_graded = holdout.loc[holdout["qualifies"] & holdout["ats_result"].notna()]

    summary = summaries(development_graded, team=team)

    league_window = _window(
        team_games,
        team=None,
        start_season=start_season,
        start_date=start_date,
        min_spread=min_spread,
        include_playoffs=include_playoffs,
        home_only=True,
    )
    league_qualifiers = league_window.loc[league_window["qualifies"]]
    road_window = _window(
        team_games,
        team=team,
        start_season=start_season,
        start_date=start_date,
        min_spread=min_spread,
        include_playoffs=include_playoffs,
        home_only=False,
    )
    road_qualifiers = road_window.loc[
        ~road_window["is_home"]
        & ~road_window["is_neutral"].fillna(False)
        & road_window["is_dog"].fillna(False)
        & road_window["dog_points"].ge(min_spread)
    ]

    long_window = _window(
        team_games,
        team=team,
        start_season=2010,
        start_date=None,
        min_spread=min_spread,
        include_playoffs=include_playoffs,
        home_only=True,
    )
    sensitivity_specs = [
        {
            "variant": "primary (calendar 2021-01-01, any home dog)",
            "start_season": start_season,
            "start_date": start_date,
            "min_spread": min_spread,
            "include_playoffs": include_playoffs,
        },
        {
            "variant": "2020 NFL season inclusive",
            "start_season": 2020,
            "start_date": None,
            "min_spread": min_spread,
            "include_playoffs": include_playoffs,
        },
        {
            "variant": "2021 NFL season onward",
            "start_season": 2021,
            "start_date": None,
            "min_spread": min_spread,
            "include_playoffs": include_playoffs,
        },
        {
            "variant": "2010+ home dogs",
            "start_season": 2010,
            "start_date": None,
            "min_spread": min_spread,
            "include_playoffs": include_playoffs,
        },
        {
            "variant": "min dog 1 point",
            "start_season": start_season,
            "start_date": start_date,
            "min_spread": 1.0,
            "include_playoffs": include_playoffs,
        },
        {
            "variant": "min dog 3 points",
            "start_season": start_season,
            "start_date": start_date,
            "min_spread": 3.0,
            "include_playoffs": include_playoffs,
        },
        {
            "variant": "regular season only",
            "start_season": start_season,
            "start_date": start_date,
            "min_spread": min_spread,
            "include_playoffs": False,
        },
    ]
    sensitivity_rows = []
    for spec in sensitivity_specs:
        variant = _window(
            team_games,
            team=team,
            start_season=spec["start_season"],
            start_date=spec["start_date"],
            min_spread=spec["min_spread"],
            include_playoffs=spec["include_playoffs"],
            home_only=True,
        )
        sensitivity_rows.append(
            record_row(
                variant.loc[variant["qualifies"]],
                variant=spec["variant"],
                start_season=spec["start_season"],
                start_date=spec["start_date"],
                min_spread=spec["min_spread"],
            )
        )

    secondary = {
        "claimed_window": pd.DataFrame(
            [
                record_row(
                    qualifiers,
                    sample="claimed_window",
                    team=team,
                    start_date=start_date,
                    start_season=start_season,
                    min_spread=min_spread,
                )
            ]
        ),
        "qualifying_games": qualifying_table(qualifiers, QUALIFYING_COLUMNS),
        "by_season": market_summary(
            graded,
            ["season"],
            "ats_result",
            "cover",
            ("team_margin", "team_ats_margin"),
        ),
        "sensitivity": pd.DataFrame(sensitivity_rows),
        "road_dogs": pd.DataFrame(
            [record_row(road_qualifiers, sample="road_dogs", team=team)]
        ),
        "longer_window": pd.DataFrame(
            [
                record_row(
                    long_window.loc[long_window["qualifies"]],
                    sample="home_dogs_2010_plus",
                    team=team,
                )
            ]
        ),
        "league_baseline": pd.DataFrame(
            [record_row(league_qualifiers, sample="league_home_dogs", team="ALL")]
        ),
        "holdout_summary": market_summary(
            holdout_graded,
            ["team"],
            "ats_result",
            "cover",
            ("team_margin", "team_ats_margin"),
        ),
    }
    metadata = metadata_for(audit, source_rows)
    metadata.update(
        {
            "team": team,
            "start_season": start_season,
            "start_date": start_date,
            "min_spread": float(min_spread),
            "include_playoffs": bool(include_playoffs),
            "site": "home",
            **claimed_counts(qualifiers),
        }
    )
    return EdgeResult(EDGE_ID, summary, audit.reset_index(drop=True), secondary, metadata)


TREND_NUMBER = "09"


def _headline(result: EdgeResult) -> str:
    meta = result.metadata
    team = meta.get("team", "")
    live = meta.get("live_strategy_rows", 0)
    if "claimed_overs" in meta:
        return (
            f"{TREND_NUMBER} {team} {meta['claimed_overs']}-{meta['claimed_unders']}-"
            f"{meta['claimed_pushes']} OVER (live {live})"
        )
    su = f"{meta.get('claimed_su_wins', 0)}-{meta.get('claimed_su_losses', 0)}"
    ats = f"{meta.get('claimed_ats_wins', 0)}-{meta.get('claimed_ats_losses', 0)}"
    su_ties = meta.get("claimed_su_ties") or 0
    ats_pushes = meta.get("claimed_ats_pushes") or 0
    if su_ties:
        su = f"{su}-{su_ties}"
    if ats_pushes:
        ats = f"{ats}-{ats_pushes}"
    return f"{TREND_NUMBER} {team} SU {su} | ATS {ats} (live {live})"


def print_report(result: EdgeResult) -> None:
    print(_headline(result))
    games = result.secondary.get("qualifying_games")
    if games is not None:
        print(games.to_string(index=False))
    if "sensitivity" in result.secondary:
        print("\nSensitivity")
        print(result.secondary["sensitivity"].to_string(index=False))


def show_notebook_tables(result: EdgeResult) -> None:
    """Display the summary and an expandable qualifying-game table.

    IPython and ipywidgets are imported in this function so the terminal
    command does not require a notebook kernel. Same split as
    scripts/opponent_stats_after_DET.py.
    """
    import ipywidgets as widgets
    from IPython.display import HTML, display

    summary = result.summary
    games = result.secondary["qualifying_games"]
    display(HTML(f"<p><strong>{_headline(result)}</strong></p>"))
    display(summary.style.hide(axis="index"))
    table_html = games.to_html(index=False)
    details = widgets.HTML(
        value=f"<p>{len(games)} qualifying games</p>{table_html}"
    )
    accordion = widgets.Accordion(children=[details], selected_index=None)
    accordion.set_title(0, f"Qualifying games ({len(games)}) — click to expand")
    display(accordion)


def show_charts(result: EdgeResult, *, notebook: bool = False) -> None:
    chart_for_result(result)
    if notebook:
        plt.show()
    else:
        plt.show(block=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Grade a team as a home underdog against closing spreads."
    )
    parser.add_argument("--team", default=DEFAULT_TEAM)
    parser.add_argument("--start-date", default=DEFAULT_START_DATE)
    parser.add_argument("--start-season", type=int, default=None)
    parser.add_argument("--min-spread", type=float, default=DEFAULT_MIN_SPREAD)
    parser.add_argument(
        "--include-playoffs",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Include playoff games (default: true).",
    )
    parser.add_argument(
        "--regular-season-only",
        action="store_true",
        help="Exclude playoff games.",
    )

    parser.add_argument(
        "--data",
        type=Path,
        default=default_games_path(),
        help="Game-level CSV (default: data/games.csv)",
    )
    parser.add_argument(
        "--notebook",
        action="store_true",
        help="Display notebook tables and inline charts",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    games = load_games(
        args.data,
        minimum_season=SITUATIONAL_MINIMUM_SEASON,
        require_scores=False,
    )
    result = analyze(
        games,
        team=args.team,
        start_season=args.start_season,
        start_date=args.start_date or None,
        min_spread=args.min_spread,
        include_playoffs=args.include_playoffs and not args.regular_season_only,
    )

    if args.notebook:
        print(_headline(result))
        show_notebook_tables(result)
    else:
        print_report(result)
    show_charts(result, notebook=args.notebook)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
