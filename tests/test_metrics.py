import math

import pandas as pd

from nfl_trends.metrics import (
    flat_bet_profit,
    grade_home_spread,
    grade_totals,
    summarize_binary_market,
    wilson_interval,
)


def test_grade_totals_marks_over_under_and_push():
    games = pd.DataFrame(
        {
            "home_score": [24, 17, 20],
            "away_score": [21, 20, 20],
            "total_line": [44.5, 40.5, 40.0],
        }
    )

    result = grade_totals(games)

    assert result["actual_total"].tolist() == [45, 37, 40]
    assert result["total_margin"].tolist() == [0.5, -3.5, 0.0]
    assert result["total_result"].tolist() == ["over", "under", "push"]


def test_grade_home_spread_uses_expected_home_margin_convention():
    games = pd.DataFrame(
        {
            "home_score": [27, 20, 24],
            "away_score": [20, 24, 21],
            "spread_line": [3.5, -4.0, 3.0],
        }
    )

    result = grade_home_spread(games)

    assert result["home_margin"].tolist() == [7, -4, 3]
    assert result["home_ats_margin"].tolist() == [3.5, 0.0, 0.0]
    assert result["home_ats_result"].tolist() == ["cover", "push", "push"]


def test_flat_bet_profit_at_minus_110():
    results = pd.Series(["win", "loss", "push", "win"])

    profits = flat_bet_profit(results, win_label="win")

    assert profits.iloc[0] == profits.iloc[3]
    assert math.isclose(profits.iloc[0], 100 / 110)
    assert profits.iloc[1] == -1.0
    assert profits.iloc[2] == 0.0


def test_binary_summary_excludes_pushes_from_rate_but_not_roi():
    results = pd.Series(["over", "under", "push", "over"])

    summary = summarize_binary_market(results, win_label="over")

    assert summary["games"] == 4
    assert summary["decisions"] == 3
    assert summary["wins"] == 2
    assert math.isclose(summary["win_rate"], 2 / 3)
    assert math.isclose(summary["roi_units"], ((100 / 110) * 2 - 1) / 4)


def test_binary_summary_ignores_null_results():
    summary = summarize_binary_market(
        pd.Series(["over", None, "push"]), win_label="over"
    )

    assert summary["games"] == 2
    assert summary["decisions"] == 1
    assert summary["wins"] == 1


def test_wilson_interval_is_bounded_and_contains_observed_rate():
    low, high = wilson_interval(6, 10)

    assert 0 <= low <= 0.6 <= high <= 1
