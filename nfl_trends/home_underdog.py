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


EDGE_ID = "home-underdog"
DEFAULT_TEAM = "PHI"
DEFAULT_START_DATE = "2021-01-01"
DEFAULT_MIN_SPREAD = 0.0
TREND_DIR = repo_root() / "trends" / "09-home-underdog"
FIGURE_NAME = "ats-margin.png"
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
        start_season=args.start_season,
        start_date=args.start_date or None,
        min_spread=args.min_spread,
        include_playoffs=args.include_playoffs and not args.regular_season_only,
    )
    paths = write_public_artifacts(result, args.output, figure_name=FIGURE_NAME)
    print_run_summary(result, paths)


if __name__ == "__main__":
    main()
