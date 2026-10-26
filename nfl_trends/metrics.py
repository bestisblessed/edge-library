from __future__ import annotations

import math

import numpy as np
import pandas as pd


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
