"""Team as an underdog of X+ points versus division opponents.

Reproduces the KillerSports/SBBreakers claim that the Eagles are 0-11 ATS since
2016 as a 2+ point dog versus NFC East foes, with tonight's home line +4.5 vs
Dallas.
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
    filter_site,
    print_run_summary,
    qualifying_table,
    record_row,
    write_public_artifacts,
)


EDGE_ID = "division-underdog"
DEFAULT_TEAM = "PHI"
DEFAULT_MIN_DOG_POINTS = 2.0
DEFAULT_START_SEASON = 2016
TREND_DIR = repo_root() / "trends" / "10-division-underdog"
FIGURE_NAME = "ats-margin.png"
QUALIFYING_COLUMNS = [
    "date",
    "season",
    "week",
    "game_id",
    "opponent",
    "home_away",
    "home_spread",
    "dog_points",
    "final_score",
    "su_result",
    "ats_result",
    "margin_vs_spread",
    "is_live",
]


def _qualifies(frame: pd.DataFrame, *, min_dog_points: float) -> pd.Series:
    return (
        frame["is_divisional"].fillna(False)
        & ~frame["is_neutral"].fillna(False)
        & frame["is_dog"].fillna(False)
        & frame["dog_points"].ge(min_dog_points)
        & frame["spread_line"].notna()
    )


def _window(
    team_games: pd.DataFrame,
    *,
    team: str | None,
    min_dog_points: float,
    start_season: int | None,
    start_date: str | None,
    site: str,
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
    window = filter_site(window, site)
    window["qualifies"] = _qualifies(window, min_dog_points=min_dog_points)
    return window


def _last_large_dog(qualifiers: pd.DataFrame, *, min_points: float) -> dict:
    completed = qualifiers.loc[
        ~qualifiers["is_live"].fillna(False) & qualifiers["dog_points"].ge(min_points)
    ].sort_values(["date", "game_id"])
    if completed.empty:
        return {
            "last_large_dog_date": None,
            "last_large_dog_opponent": None,
            "last_large_dog_points": None,
            "last_large_dog_game_id": None,
        }
    row = completed.iloc[-1]
    return {
        "last_large_dog_date": pd.Timestamp(row["date"]).strftime("%Y-%m-%d"),
        "last_large_dog_opponent": row["opponent"],
        "last_large_dog_points": float(row["dog_points"]),
        "last_large_dog_game_id": row["game_id"],
    }


def analyze(
    games: pd.DataFrame,
    *,
    team: str = DEFAULT_TEAM,
    min_dog_points: float = DEFAULT_MIN_DOG_POINTS,
    start_season: int | None = DEFAULT_START_SEASON,
    start_date: str | None = None,
    site: str = "both",
    include_playoffs: bool = True,
) -> EdgeResult:
    source_rows = len(games)
    team_games = expand_team_games(games)
    audit = _window(
        team_games,
        team=team,
        min_dog_points=min_dog_points,
        start_season=start_season,
        start_date=start_date,
        site=site,
        include_playoffs=include_playoffs,
    )
    if audit.empty:
        raise ValueError(f"No games for {team} in the requested window")

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
        ("team_margin", "team_ats_margin", "dog_points"),
    )
    if summary.empty:
        summary = pd.DataFrame([record_row(development_graded, team=team)])
    if "sample" not in summary.columns:
        summary.insert(1, "sample", "development")

    live = qualifiers.loc[qualifiers["is_live"].fillna(False)]
    tonight_points = (
        float(live["dog_points"].max()) if not live.empty else float(min_dog_points)
    )
    last_large = _last_large_dog(
        audit.loc[
            audit["is_divisional"].fillna(False)
            & ~audit["is_neutral"].fillna(False)
            & audit["is_dog"].fillna(False)
        ],
        min_points=tonight_points,
    )

    league_window = _window(
        team_games,
        team=None,
        min_dog_points=min_dog_points,
        start_season=start_season,
        start_date=start_date,
        site=site,
        include_playoffs=include_playoffs,
    )
    sensitivity_specs = [
        {
            "variant": "primary (2+ point division dog, 2016+)",
            "min_dog_points": min_dog_points,
            "site": site,
            "start_season": start_season,
        },
        {
            "variant": "1+ point division dog",
            "min_dog_points": 1.0,
            "site": site,
            "start_season": start_season,
        },
        {
            "variant": "3+ point division dog",
            "min_dog_points": 3.0,
            "site": site,
            "start_season": start_season,
        },
        {
            "variant": "home 2+ point division dogs",
            "min_dog_points": min_dog_points,
            "site": "home",
            "start_season": start_season,
        },
        {
            "variant": "road 2+ point division dogs",
            "min_dog_points": min_dog_points,
            "site": "road",
            "start_season": start_season,
        },
        {
            "variant": "regular season only",
            "min_dog_points": min_dog_points,
            "site": site,
            "start_season": start_season,
            "include_playoffs": False,
        },
    ]
    sensitivity_rows = []
    for spec in sensitivity_specs:
        variant = _window(
            team_games,
            team=team,
            min_dog_points=spec["min_dog_points"],
            start_season=spec["start_season"],
            start_date=start_date,
            site=spec["site"],
            include_playoffs=spec.get("include_playoffs", include_playoffs),
        )
        sensitivity_rows.append(
            record_row(
                variant.loc[variant["qualifies"]],
                variant=spec["variant"],
                min_dog_points=spec["min_dog_points"],
                site=spec["site"],
            )
        )

    secondary = {
        "claimed_window": pd.DataFrame(
            [
                record_row(
                    qualifiers,
                    sample="claimed_window",
                    team=team,
                    min_dog_points=min_dog_points,
                    start_season=start_season,
                    site=site,
                )
            ]
        ),
        "qualifying_games": qualifying_table(qualifiers, QUALIFYING_COLUMNS),
        "by_season": market_summary(
            graded,
            ["season"],
            "ats_result",
            "cover",
            ("team_margin", "team_ats_margin", "dog_points"),
        ),
        "sensitivity": pd.DataFrame(sensitivity_rows),
        "league_baseline": pd.DataFrame(
            [
                record_row(
                    league_window.loc[league_window["qualifies"]],
                    sample="league_division_dogs",
                    team="ALL",
                    min_dog_points=min_dog_points,
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
            "min_dog_points": float(min_dog_points),
            "start_season": start_season,
            "start_date": start_date,
            "site": site,
            "include_playoffs": bool(include_playoffs),
            "tonight_dog_points": tonight_points if not live.empty else None,
            "tonight_game_ids": ",".join(live["game_id"].astype(str))
            if not live.empty
            else "",
            **last_large,
            **claimed_counts(qualifiers),
        }
    )
    return EdgeResult(EDGE_ID, summary, audit.reset_index(drop=True), secondary, metadata)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Grade a team as an X+ point underdog versus division opponents."
    )
    parser.add_argument("--team", default=DEFAULT_TEAM)
    parser.add_argument("--min-dog-points", type=float, default=DEFAULT_MIN_DOG_POINTS)
    parser.add_argument("--start-season", type=int, default=DEFAULT_START_SEASON)
    parser.add_argument("--start-date", default=None)
    parser.add_argument("--site", choices=("home", "road", "both"), default="both")
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
        min_dog_points=args.min_dog_points,
        start_season=args.start_season,
        start_date=args.start_date,
        site=args.site,
        include_playoffs=args.include_playoffs and not args.regular_season_only,
    )
    paths = write_public_artifacts(result, args.output, figure_name=FIGURE_NAME)
    print_run_summary(result, paths)


if __name__ == "__main__":
    main()
