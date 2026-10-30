#!/usr/bin/env python3
"""Rested-after-scoring totals.

Reproduces the KillerSports situational claim that Lions games have gone
OVER after extra rest following a 24-plus-point game.

Default filter
--------------
- Team: DET
- Game date on or after 2020-12-01
- More than normal rest: nflverse ``home_rest`` / ``away_rest`` >= 8
  (normal Sunday-to-Sunday rest is 7; this includes byes and extra rest
  after Thursday/Monday games)
- Previous game for this team scored >= 24 points
- Previous game is in the same season (bye and short-week rest are
  intra-season; week-1 nflverse rest is typically 7 anyway)
- Result: OVER / UNDER / PUSH vs the closing ``total_line``
- Playoffs are included; preseason is not present in ``data/games.csv``

Live games (no final score yet) can still qualify and are listed but not
graded. Sensitivity variants (>=10 rest, bye-only >=13, rest >=14, and
cross-season prior games) are published alongside a league-wide baseline.

Reads only ``data/games.csv`` (repo-root relative). Run from the repository root:

    python scripts/lions_extra_rest_after_scoring.py
    python scripts/lions_extra_rest_after_scoring.py --notebook
"""

# Source: @SBBreakers, 2026-10-25 — https://x.com/SBBreakers/status/2114383482868658651

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

EDGE_ID = "rested-after-scoring-totals"
DEFAULT_TEAM = "DET"
DEFAULT_START_DATE = "2020-12-01"
NORMAL_REST_DAYS = 7
DEFAULT_MIN_REST_DAYS = NORMAL_REST_DAYS + 1
DEFAULT_MIN_PRIOR_POINTS = 24
BYE_REST_DAYS = 13
QUALIFYING_COLUMNS = [
    "date",
    "season",
    "week",
    "game_id",
    "team",
    "opponent",
    "home_away",
    "rest_days",
    "prior_game_date",
    "prior_opponent",
    "prior_team_points",
    "total_line",
    "team_score",
    "opponent_score",
    "combined_points",
    "result",
    "margin_vs_total",
    "is_live",
]


def expand_team_games(games: pd.DataFrame) -> pd.DataFrame:
    """Stack home and away views and attach same-team lag features."""
    if "date" not in games.columns:
        raise ValueError("games missing required column: date")
    if "home_rest" not in games.columns or "away_rest" not in games.columns:
        raise ValueError("games missing required columns: home_rest, away_rest")

    frame = games.copy()
    frame["date"] = pd.to_datetime(frame["date"], errors="raise")
    keep = [
        column
        for column in (
            "game_id",
            "season",
            "week",
            "game_type",
            "date",
            "home_team",
            "away_team",
            "home_score",
            "away_score",
            "total_line",
            "spread_line",
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
        rest_days=frame["home_rest"],
        is_home=True,
    )
    away = frame.loc[:, keep].assign(
        team=frame["away_team"],
        opponent=frame["home_team"],
        team_score=frame["away_score"],
        opponent_score=frame["home_score"],
        rest_days=frame["away_rest"],
        is_home=False,
    )
    team_games = pd.concat([home, away], ignore_index=True)
    team_games = team_games.sort_values(["team", "date", "game_id"]).reset_index(
        drop=True
    )
    grouped = team_games.groupby("team", sort=False)
    team_games["prior_team_score"] = grouped["team_score"].shift(1)
    team_games["prior_date"] = grouped["date"].shift(1)
    team_games["prior_season"] = grouped["season"].shift(1)
    team_games["prior_opponent"] = grouped["opponent"].shift(1)
    team_games["calendar_rest"] = (team_games["date"] - team_games["prior_date"]).dt.days
    team_games["same_season_prior"] = team_games["prior_season"].eq(team_games["season"])
    team_games["home_away"] = team_games["is_home"].map({True: "vs", False: "@"})
    team_games["is_live"] = team_games["team_score"].isna() | team_games[
        "opponent_score"
    ].isna()
    return team_games


def _qualifies(
    frame: pd.DataFrame,
    *,
    min_rest_days: int,
    min_prior_points: int,
    same_season_prior: bool,
) -> pd.Series:
    flags = (
        frame["rest_days"].ge(min_rest_days).fillna(False)
        & frame["prior_team_score"].ge(min_prior_points).fillna(False)
    )
    if same_season_prior:
        flags = flags & frame["same_season_prior"].fillna(False)
    return flags


def _apply_window(
    team_games: pd.DataFrame,
    *,
    team: str | None,
    min_rest_days: int,
    min_prior_points: int,
    start_date: str,
    same_season_prior: bool,
) -> pd.DataFrame:
    start = pd.Timestamp(start_date)
    window = team_games.loc[team_games["date"].ge(start)].copy()
    if team is not None:
        window = window.loc[window["team"].eq(team)].copy()
    window["qualifies"] = _qualifies(
        window,
        min_rest_days=min_rest_days,
        min_prior_points=min_prior_points,
        same_season_prior=same_season_prior,
    )
    return window


def _grade_completed(frame: pd.DataFrame) -> pd.DataFrame:
    graded = grade_totals(frame)
    ungradable = (
        graded["home_score"].isna()
        | graded["away_score"].isna()
        | graded["total_line"].isna()
        | graded["total_margin"].isna()
    )
    graded.loc[ungradable, "total_result"] = pd.NA
    return graded


def _market_row(frame: pd.DataFrame, **dimensions) -> dict:
    graded = frame.loc[frame["total_result"].notna()]
    row = dict(dimensions)
    row.update(summarize_binary_market(graded["total_result"], win_label="over"))
    if graded.empty:
        row["avg_actual_total"] = float("nan")
        row["avg_total_line"] = float("nan")
        row["avg_total_margin"] = float("nan")
    else:
        row["avg_actual_total"] = float(graded["actual_total"].mean())
        row["avg_total_line"] = float(graded["total_line"].mean())
        row["avg_total_margin"] = float(graded["total_margin"].mean())
    row["live_games"] = int(frame["is_live"].fillna(False).sum())
    return row


def qualifying_games_table(frame: pd.DataFrame) -> pd.DataFrame:
    table = frame.loc[frame["qualifies"]].copy()
    table = table.rename(
        columns={
            "prior_date": "prior_game_date",
            "prior_team_score": "prior_team_points",
            "opponent_score": "opponent_score",
            "actual_total": "combined_points",
            "total_result": "result",
            "total_margin": "margin_vs_total",
        }
    )
    missing = [column for column in QUALIFYING_COLUMNS if column not in table.columns]
    for column in missing:
        table[column] = pd.NA
    table = table.loc[:, QUALIFYING_COLUMNS].sort_values(["date", "game_id"])
    table["date"] = pd.to_datetime(table["date"]).dt.strftime("%Y-%m-%d")
    if "prior_game_date" in table.columns:
        table["prior_game_date"] = pd.to_datetime(
            table["prior_game_date"], errors="coerce"
        ).dt.strftime("%Y-%m-%d")
    return table.reset_index(drop=True)


def summaries(development_graded: pd.DataFrame, *, team: str) -> pd.DataFrame:
    summary = market_summary(
        development_graded,
        ["team"],
        "total_result",
        "over",
        ("actual_total", "total_line", "total_margin"),
    )
    if summary.empty:
        summary = pd.DataFrame([_market_row(development_graded, team=team)])
    summary.insert(1, "sample", "development")
    return summary


def analyze(
    games: pd.DataFrame,
    *,
    team: str = DEFAULT_TEAM,
    min_prior_points: int = DEFAULT_MIN_PRIOR_POINTS,
    min_rest_days: int = DEFAULT_MIN_REST_DAYS,
    start_date: str = DEFAULT_START_DATE,
    same_season_prior: bool = True,
) -> EdgeResult:
    source_rows = len(games)
    team_games = expand_team_games(games)
    audit = _apply_window(
        team_games,
        team=team,
        min_rest_days=min_rest_days,
        min_prior_points=min_prior_points,
        start_date=start_date,
        same_season_prior=same_season_prior,
    )
    if audit.empty:
        raise ValueError(f"No team-games for {team} on or after {start_date}")
    audit = _grade_completed(audit)

    qualifiers = audit.loc[audit["qualifies"]].copy()
    graded_qualifiers = qualifiers.loc[qualifiers["total_result"].notna()].copy()
    development, holdout = split_research_frame(audit)
    development_graded = development.loc[
        development["qualifies"] & development["total_result"].notna()
    ]
    holdout_graded = holdout.loc[holdout["qualifies"] & holdout["total_result"].notna()]

    summary = summaries(development_graded, team=team)

    league_window = _apply_window(
        team_games,
        team=None,
        min_rest_days=min_rest_days,
        min_prior_points=min_prior_points,
        start_date=start_date,
        same_season_prior=same_season_prior,
    )
    league_window = _grade_completed(league_window)
    league_qualifiers = league_window.loc[league_window["qualifies"]].copy()
    league_rows = [_market_row(league_qualifiers, team="ALL")]
    for team_name, group in league_qualifiers.groupby(
        "team", observed=True, dropna=False
    ):
        league_rows.append(_market_row(group, team=team_name))
    league_baseline = pd.DataFrame(league_rows)

    sensitivity_specs = [
        {
            "variant": "primary (>=8 rest, 24+ prior, same-season, Dec 2020+)",
            "min_rest_days": min_rest_days,
            "min_prior_points": min_prior_points,
            "same_season_prior": same_season_prior,
            "start_date": start_date,
        },
        {
            "variant": "rest >= 10",
            "min_rest_days": 10,
            "min_prior_points": min_prior_points,
            "same_season_prior": same_season_prior,
            "start_date": start_date,
        },
        {
            "variant": "bye-only (rest >= 13)",
            "min_rest_days": BYE_REST_DAYS,
            "min_prior_points": min_prior_points,
            "same_season_prior": same_season_prior,
            "start_date": start_date,
        },
        {
            "variant": "rest >= 14",
            "min_rest_days": 14,
            "min_prior_points": min_prior_points,
            "same_season_prior": same_season_prior,
            "start_date": start_date,
        },
        {
            "variant": "cross-season prior game allowed",
            "min_rest_days": min_rest_days,
            "min_prior_points": min_prior_points,
            "same_season_prior": False,
            "start_date": start_date,
        },
        {
            "variant": "from 2020-01-01 (no December cut)",
            "min_rest_days": min_rest_days,
            "min_prior_points": min_prior_points,
            "same_season_prior": same_season_prior,
            "start_date": "2020-01-01",
        },
    ]
    sensitivity_rows = []
    for spec in sensitivity_specs:
        variant_window = _apply_window(
            team_games,
            team=team,
            min_rest_days=spec["min_rest_days"],
            min_prior_points=spec["min_prior_points"],
            start_date=spec["start_date"],
            same_season_prior=spec["same_season_prior"],
        )
        variant_window = _grade_completed(variant_window)
        variant_qualifiers = variant_window.loc[variant_window["qualifies"]]
        sensitivity_rows.append(
            _market_row(
                variant_qualifiers,
                variant=spec["variant"],
                min_rest_days=spec["min_rest_days"],
                min_prior_points=spec["min_prior_points"],
                same_season_prior=spec["same_season_prior"],
                start_date=spec["start_date"],
            )
        )

    claimed_window = pd.DataFrame(
        [
            _market_row(
                qualifiers,
                sample="claimed_window",
                team=team,
                min_rest_days=min_rest_days,
                min_prior_points=min_prior_points,
                start_date=start_date,
            )
        ]
    )
    secondary = {
        "claimed_window": claimed_window,
        "qualifying_games": qualifying_games_table(qualifiers),
        "by_season": market_summary(
            graded_qualifiers,
            ["season"],
            "total_result",
            "over",
            ("actual_total", "total_line", "total_margin"),
        ),
        "sensitivity": pd.DataFrame(sensitivity_rows),
        "league_baseline": league_baseline.sort_values(
            ["wins", "games"], ascending=False
        ).reset_index(drop=True),
        "holdout_summary": market_summary(
            holdout_graded,
            ["team"],
            "total_result",
            "over",
            ("actual_total", "total_line", "total_margin"),
        ),
    }
    metadata = metadata_for(audit, source_rows)
    metadata.update(
        {
            "team": team,
            "min_rest_days": int(min_rest_days),
            "min_prior_points": int(min_prior_points),
            "start_date": start_date,
            "same_season_prior": bool(same_season_prior),
            "normal_rest_days": NORMAL_REST_DAYS,
            "bye_rest_days": BYE_REST_DAYS,
            "strategy_rows": int(len(qualifiers)),
            "graded_strategy_rows": int(len(graded_qualifiers)),
            "live_strategy_rows": int(qualifiers["is_live"].fillna(False).sum()),
            "claimed_overs": int((graded_qualifiers["total_result"] == "over").sum()),
            "claimed_unders": int((graded_qualifiers["total_result"] == "under").sum()),
            "claimed_pushes": int((graded_qualifiers["total_result"] == "push").sum()),
        }
    )
    return EdgeResult(
        EDGE_ID, summary, audit.reset_index(drop=True), secondary, metadata
    )


TREND_NUMBER = "08"


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
        description="Grade extra-rest-after-scoring totals against closing lines."
    )
    parser.add_argument("--team", default=DEFAULT_TEAM)
    parser.add_argument("--min-prior-points", type=int, default=DEFAULT_MIN_PRIOR_POINTS)
    parser.add_argument("--min-rest-days", type=int, default=DEFAULT_MIN_REST_DAYS)
    parser.add_argument("--start-date", default=DEFAULT_START_DATE)
    parser.add_argument(
        "--allow-cross-season-prior",
        action="store_true",
        help="Allow the previous game to come from a prior season.",
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
    games = load_games(args.data, require_scores=False)
    result = analyze(
        games,
        team=args.team,
        min_prior_points=args.min_prior_points,
        min_rest_days=args.min_rest_days,
        start_date=args.start_date,
        same_season_prior=not args.allow_cross_season_prior,
    )

    if args.notebook:
        print(_headline(result))
        show_notebook_tables(result)
    else:
        print_report(result)
    show_charts(result, notebook=args.notebook)
    return 0


def select_seasons(result: EdgeResult, seasons) -> EdgeResult:
    """Filter the already calculated history, preserving prior-game context."""
    result.audit = result.audit.loc[result.audit["season"].isin(seasons)].copy()
    qualifiers = result.audit.loc[result.audit["qualifies"]].copy()
    graded = qualifiers.loc[qualifiers["total_result"].notna()]
    result.metadata.update({"claimed_overs": int(graded.total_result.eq("over").sum()), "claimed_unders": int(graded.total_result.eq("under").sum()), "claimed_pushes": int(graded.total_result.eq("push").sum()), "live_strategy_rows": int(qualifiers.is_live.sum())})
    result.summary = pd.DataFrame([_market_row(qualifiers, team=result.metadata["team"])])
    result.secondary["qualifying_games"] = qualifying_games_table(qualifiers)
    return result


if __name__ == "__main__":
    raise SystemExit(main())
