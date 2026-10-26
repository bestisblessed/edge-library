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
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from nfl_trends.charts import chart_for_result
from nfl_trends.common import market_summary, metadata_for, split_research_frame
from nfl_trends.games import default_games_path, load_games, repo_root
from nfl_trends.metrics import grade_totals, summarize_binary_market
from nfl_trends.models import EdgeResult


EDGE_ID = "rested-after-scoring-totals"
DEFAULT_TEAM = "DET"
DEFAULT_START_DATE = "2020-12-01"
NORMAL_REST_DAYS = 7
DEFAULT_MIN_REST_DAYS = NORMAL_REST_DAYS + 1
DEFAULT_MIN_PRIOR_POINTS = 24
BYE_REST_DAYS = 13
TREND_DIR = repo_root() / "trends" / "08-rested-after-scoring-totals"
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


def write_public_artifacts(
    result: EdgeResult, dest: Path | str | None = None
) -> dict[str, Path]:
    """Write the human-facing qualifying CSV and scatter PNG into the trend folder."""
    target = Path(dest) if dest is not None else TREND_DIR
    figures = target / "figures"
    figures.mkdir(parents=True, exist_ok=True)
    csv_path = target / "qualifying_games.csv"
    png_path = figures / "combined-points-vs-total.png"
    result.secondary["qualifying_games"].to_csv(csv_path, index=False)
    figure = chart_for_result(result)
    figure.savefig(png_path, dpi=160, bbox_inches="tight", facecolor="white")
    plt.close(figure)
    return {"qualifying_games": csv_path, "chart": png_path}


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
        "--output",
        type=Path,
        default=TREND_DIR,
        help="Directory for qualifying_games.csv and figures/ PNG.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    games = load_games(default_games_path(), require_scores=False)
    result = analyze(
        games,
        team=args.team,
        min_prior_points=args.min_prior_points,
        min_rest_days=args.min_rest_days,
        start_date=args.start_date,
        same_season_prior=not args.allow_cross_season_prior,
    )
    paths = write_public_artifacts(result, args.output)
    overs = result.metadata["claimed_overs"]
    unders = result.metadata["claimed_unders"]
    pushes = result.metadata["claimed_pushes"]
    live = result.metadata["live_strategy_rows"]
    print(
        f"{result.metadata['team']} {overs}-{unders}-{pushes} "
        f"(live qualifiers: {live})"
    )
    print(result.secondary["qualifying_games"].to_string(index=False))
    print("\nSensitivity")
    print(result.secondary["sensitivity"].to_string(index=False))
    print(f"CSV: {paths['qualifying_games']}")
    print(f"PNG: {paths['chart']}")


if __name__ == "__main__":
    main()
