"""Shared helpers for parameterized situational betting audits."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from nfl_trends.charts import chart_for_result
from nfl_trends.divisions import TEAM_TO_DIVISION
from nfl_trends.metrics import summarize_binary_market
from nfl_trends.models import EdgeResult


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


def write_public_artifacts(
    result: EdgeResult,
    dest: Path | str,
    *,
    figure_name: str,
) -> dict[str, Path]:
    target = Path(dest)
    figures = target / "figures"
    figures.mkdir(parents=True, exist_ok=True)
    csv_path = target / "qualifying_games.csv"
    png_path = figures / figure_name
    result.secondary["qualifying_games"].to_csv(csv_path, index=False)
    figure = chart_for_result(result)
    figure.savefig(png_path, dpi=160, bbox_inches="tight", facecolor="white")
    plt.close(figure)
    return {"qualifying_games": csv_path, "chart": png_path}


def print_run_summary(result: EdgeResult, paths: dict[str, Path]) -> None:
    meta = result.metadata
    print(
        f"{meta.get('team', '')} SU "
        f"{meta.get('claimed_su_wins', 0)}-{meta.get('claimed_su_losses', 0)}"
        f"{'' if not meta.get('claimed_su_ties') else '-' + str(meta['claimed_su_ties'])} | "
        f"ATS {meta.get('claimed_ats_wins', 0)}-{meta.get('claimed_ats_losses', 0)}"
        f"{'' if not meta.get('claimed_ats_pushes') else '-' + str(meta['claimed_ats_pushes'])} "
        f"(live {meta.get('live_strategy_rows', 0)})"
    )
    print(result.secondary["qualifying_games"].to_string(index=False))
    if "sensitivity" in result.secondary:
        print("\nSensitivity")
        print(result.secondary["sensitivity"].to_string(index=False))
    print(f"CSV: {paths['qualifying_games']}")
    print(f"PNG: {paths['chart']}")
