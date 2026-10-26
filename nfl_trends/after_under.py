"""After the previous game went under the total by N+ points.

Reproduces the KillerSports/SBBreakers claim that the Cowboys are 6-0 ATS and
6-0 SU since December 2021 after a 10-point under, with average win and cover
margins of 19.8 and 14.8.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from nfl_trends.common import market_summary, metadata_for, split_research_frame
from nfl_trends.games import (
    SITUATIONAL_MINIMUM_SEASON,
    default_games_path,
    load_games,
    repo_root,
)
from nfl_trends.models import EdgeResult
from nfl_trends.situational import (
    apply_time_window,
    claimed_counts,
    expand_team_games,
    print_run_summary,
    qualifying_table,
    record_row,
    write_public_artifacts,
)


EDGE_ID = "after-under"
DEFAULT_TEAM = "DAL"
DEFAULT_MIN_UNDER_MARGIN = 10.0
DEFAULT_START_DATE = "2021-12-01"
TREND_DIR = repo_root() / "trends" / "11-after-under"
FIGURE_NAME = "ats-margin.png"
QUALIFYING_COLUMNS = [
    "date",
    "season",
    "week",
    "game_id",
    "opponent",
    "home_away",
    "home_spread",
    "final_score",
    "su_result",
    "ats_result",
    "win_margin",
    "margin_vs_spread",
    "prior_game_date",
    "prior_opponent",
    "prior_combined_points",
    "prior_total_line",
    "prior_under_margin",
    "is_live",
]


def _qualifies(
    frame: pd.DataFrame,
    *,
    min_under_margin: float,
    same_season_prior: bool,
) -> pd.Series:
    flags = frame["prior_under_margin"].ge(min_under_margin).fillna(False)
    if same_season_prior:
        flags = flags & frame["same_season_prior"].fillna(False)
    return flags


def _window(
    team_games: pd.DataFrame,
    *,
    team: str | None,
    min_under_margin: float,
    start_season: int | None,
    start_date: str | None,
    same_season_prior: bool,
    include_playoffs: bool,
) -> pd.DataFrame:
    window = apply_time_window(
        team_games,
        start_season=start_season,
        start_date=start_date,
        include_playoffs=include_playoffs,
    )
    if team is not None:
        window = window.loc[window["team"].eq(team)].copy()
    window["qualifies"] = _qualifies(
        window,
        min_under_margin=min_under_margin,
        same_season_prior=same_season_prior,
    )
    return window


def analyze(
    games: pd.DataFrame,
    *,
    team: str = DEFAULT_TEAM,
    min_under_margin: float = DEFAULT_MIN_UNDER_MARGIN,
    start_date: str | None = DEFAULT_START_DATE,
    start_season: int | None = None,
    same_season_prior: bool = True,
    include_playoffs: bool = True,
) -> EdgeResult:
    source_rows = len(games)
    team_games = expand_team_games(games)
    audit = _window(
        team_games,
        team=team,
        min_under_margin=min_under_margin,
        start_season=start_season,
        start_date=start_date,
        same_season_prior=same_season_prior,
        include_playoffs=include_playoffs,
    )
    if audit.empty:
        raise ValueError(f"No team-games for {team} in the requested window")

    qualifiers = audit.loc[audit["qualifies"]].copy()
    graded = qualifiers.loc[qualifiers["ats_result"].notna()].copy()
    development, holdout = split_research_frame(audit)
    development_graded = development.loc[
        development["qualifies"] & development["ats_result"].notna()
    ]
    holdout_graded = holdout.loc[holdout["qualifies"] & holdout["ats_result"].notna()]

    summary = market_summary(
        development_graded,
        ["team"],
        "ats_result",
        "cover",
        ("team_margin", "team_ats_margin", "prior_under_margin"),
    )
    if summary.empty:
        summary = pd.DataFrame([record_row(development_graded, team=team)])
    if "sample" not in summary.columns:
        summary.insert(1, "sample", "development")

    live = qualifiers.loc[qualifiers["is_live"].fillna(False)]
    last_completed = (
        audit.loc[~audit["is_live"].fillna(False)]
        .sort_values(["date", "game_id"])
        .tail(1)
    )

    league_window = _window(
        team_games,
        team=None,
        min_under_margin=min_under_margin,
        start_season=start_season,
        start_date=start_date,
        same_season_prior=same_season_prior,
        include_playoffs=include_playoffs,
    )
    sensitivity_specs = [
        {
            "variant": "primary (>=10 under, same-season, Dec 2021+)",
            "min_under_margin": min_under_margin,
            "start_date": start_date,
            "same_season_prior": same_season_prior,
        },
        {
            "variant": "under by 7+",
            "min_under_margin": 7.0,
            "start_date": start_date,
            "same_season_prior": same_season_prior,
        },
        {
            "variant": "under by 14+",
            "min_under_margin": 14.0,
            "start_date": start_date,
            "same_season_prior": same_season_prior,
        },
        {
            "variant": "strictly more than 10 (excludes exact 10)",
            "min_under_margin": 10.5,
            "start_date": start_date,
            "same_season_prior": same_season_prior,
        },
        {
            "variant": "no date cut",
            "min_under_margin": min_under_margin,
            "start_date": None,
            "same_season_prior": same_season_prior,
        },
        {
            "variant": "cross-season prior allowed",
            "min_under_margin": min_under_margin,
            "start_date": start_date,
            "same_season_prior": False,
        },
    ]
    sensitivity_rows = []
    for spec in sensitivity_specs:
        variant = _window(
            team_games,
            team=team,
            min_under_margin=spec["min_under_margin"],
            start_season=start_season,
            start_date=spec["start_date"],
            same_season_prior=spec["same_season_prior"],
            include_playoffs=include_playoffs,
        )
        sensitivity_rows.append(
            record_row(
                variant.loc[variant["qualifies"]],
                variant=spec["variant"],
                min_under_margin=spec["min_under_margin"],
                start_date=spec["start_date"],
                same_season_prior=spec["same_season_prior"],
            )
        )

    secondary = {
        "claimed_window": pd.DataFrame(
            [
                record_row(
                    qualifiers,
                    sample="claimed_window",
                    team=team,
                    min_under_margin=min_under_margin,
                    start_date=start_date,
                    same_season_prior=same_season_prior,
                )
            ]
        ),
        "qualifying_games": qualifying_table(qualifiers, QUALIFYING_COLUMNS),
        "by_season": market_summary(
            graded,
            ["season"],
            "ats_result",
            "cover",
            ("team_margin", "team_ats_margin", "prior_under_margin"),
        ),
        "sensitivity": pd.DataFrame(sensitivity_rows),
        "league_baseline": pd.DataFrame(
            [
                record_row(
                    league_window.loc[league_window["qualifies"]],
                    sample="league_after_under",
                    team="ALL",
                    min_under_margin=min_under_margin,
                )
            ]
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
            "min_under_margin": float(min_under_margin),
            "start_date": start_date,
            "start_season": start_season,
            "same_season_prior": bool(same_season_prior),
            "include_playoffs": bool(include_playoffs),
            "last_game_id": (
                str(last_completed.iloc[0]["game_id"])
                if not last_completed.empty
                else None
            ),
            "last_game_under_margin": (
                None
                if last_completed.empty
                else (
                    None
                    if pd.isna(last_completed.iloc[0]["under_margin"])
                    else float(last_completed.iloc[0]["under_margin"])
                )
            ),
            "last_game_total_line": (
                None
                if last_completed.empty
                or pd.isna(last_completed.iloc[0].get("total_line"))
                else float(last_completed.iloc[0]["total_line"])
            ),
            "last_game_actual_total": (
                None
                if last_completed.empty or pd.isna(last_completed.iloc[0]["actual_total"])
                else float(last_completed.iloc[0]["actual_total"])
            ),
            "tonight_qualifies": bool(len(live) > 0),
            "tonight_game_ids": ",".join(live["game_id"].astype(str))
            if not live.empty
            else "",
            "tonight_prior_under_margin": (
                None
                if live.empty or pd.isna(live.iloc[0]["prior_under_margin"])
                else float(live.iloc[0]["prior_under_margin"])
            ),
            **claimed_counts(qualifiers),
        }
    )
    return EdgeResult(EDGE_ID, summary, audit.reset_index(drop=True), secondary, metadata)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Grade games after the previous contest went under the total by N+ points."
    )
    parser.add_argument("--team", default=DEFAULT_TEAM)
    parser.add_argument(
        "--min-under-margin", type=float, default=DEFAULT_MIN_UNDER_MARGIN
    )
    parser.add_argument("--start-date", default=DEFAULT_START_DATE)
    parser.add_argument("--start-season", type=int, default=None)
    parser.add_argument(
        "--allow-cross-season-prior",
        action="store_true",
        help="Allow the previous game to come from a prior season.",
    )
    parser.add_argument(
        "--include-playoffs",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Include playoff games (default: true).",
    )
    parser.add_argument("--regular-season-only", action="store_true")
    parser.add_argument("--output", type=Path, default=TREND_DIR)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    games = load_games(
        default_games_path(),
        minimum_season=SITUATIONAL_MINIMUM_SEASON,
        require_scores=False,
    )
    result = analyze(
        games,
        team=args.team,
        min_under_margin=args.min_under_margin,
        start_date=args.start_date or None,
        start_season=args.start_season,
        same_season_prior=not args.allow_cross_season_prior,
        include_playoffs=args.include_playoffs and not args.regular_season_only,
    )
    paths = write_public_artifacts(result, args.output, figure_name=FIGURE_NAME)
    print_run_summary(result, paths)


if __name__ == "__main__":
    main()
