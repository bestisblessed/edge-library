import pandas as pd
import pytest
from matplotlib import pyplot as plt

from conftest import load_script
from test_rested_after_scoring import rested_after_scoring_games
from test_situational_trends import (
    after_under_games,
    division_underdog_games,
    home_underdog_games,
)

rested_after_scoring = load_script("08_rested_after_scoring")
home_underdog = load_script("09_home_underdog")
division_underdog = load_script("10_division_underdog")
after_under = load_script("11_after_under")
chart_for_result = rested_after_scoring.chart_for_result
write_public_artifacts = home_underdog.write_public_artifacts
EdgeResult = rested_after_scoring.EdgeResult
SITUATIONAL_MINIMUM_SEASON = rested_after_scoring.SITUATIONAL_MINIMUM_SEASON
default_games_path = rested_after_scoring.default_games_path
load_games = rested_after_scoring.load_games


def test_every_ported_trend_runs_and_produces_a_labeled_primary_chart():
    games_totals = load_games(default_games_path(), require_scores=False)
    games_situational = load_games(
        default_games_path(),
        minimum_season=SITUATIONAL_MINIMUM_SEASON,
        require_scores=False,
    )
    results = [
        rested_after_scoring.analyze(games_totals),
        home_underdog.analyze(games_situational),
        division_underdog.analyze(games_situational),
        after_under.analyze(games_situational),
    ]

    assert {result.id for result in results} == {
        "rested-after-scoring-totals",
        "home-underdog",
        "division-underdog",
        "after-under",
    }
    for result in results:
        assert not result.summary.empty
        assert int(result.metadata["included_rows"]) > 0
        figure = chart_for_result(result)
        try:
            assert figure.axes
            assert figure.axes[0].get_title()
            assert figure.axes[0].get_xlabel()
            assert figure.axes[0].get_ylabel()
        finally:
            plt.close(figure)


@pytest.mark.parametrize(
    ("analyze", "games_fn", "edge_id"),
    [
        (
            rested_after_scoring.analyze,
            rested_after_scoring_games,
            "rested-after-scoring-totals",
        ),
        (home_underdog.analyze, home_underdog_games, "home-underdog"),
        (division_underdog.analyze, division_underdog_games, "division-underdog"),
        (after_under.analyze, after_under_games, "after-under"),
    ],
)
def test_fixture_games_produce_a_labeled_chart(analyze, games_fn, edge_id):
    result = analyze(games_fn())
    figure = chart_for_result(result)
    try:
        assert result.id == edge_id
        assert figure.axes
        assert figure.axes[0].get_title()
        assert figure.axes[0].get_xlabel()
        assert figure.axes[0].get_ylabel()
    finally:
        plt.close(figure)


@pytest.mark.parametrize(
    ("analyze", "games_fn", "figure_name"),
    [
        (
            rested_after_scoring.analyze,
            rested_after_scoring_games,
            "combined-points-vs-total.png",
        ),
        (home_underdog.analyze, home_underdog_games, "ats-margin.png"),
        (division_underdog.analyze, division_underdog_games, "ats-margin.png"),
        (after_under.analyze, after_under_games, "ats-margin.png"),
    ],
)
def test_write_public_artifacts_writes_csv_and_png(
    tmp_path, analyze, games_fn, figure_name
):
    result = analyze(games_fn())
    if result.id == "rested-after-scoring-totals":
        paths = rested_after_scoring.write_public_artifacts(result, tmp_path)
    else:
        paths = write_public_artifacts(result, tmp_path, figure_name=figure_name)

    assert paths["qualifying_games"].is_file()
    assert paths["chart"].is_file()
    assert paths["chart"].name == figure_name
    saved = pd.read_csv(paths["qualifying_games"])
    assert not saved.empty
    assert "game_id" in saved.columns


def test_chart_for_result_rejects_unported_edges():
    result = EdgeResult(
        id="weather-wind-totals",
        summary=pd.DataFrame(),
        audit=pd.DataFrame(),
    )

    with pytest.raises(ValueError, match="No chart contract"):
        chart_for_result(result)
