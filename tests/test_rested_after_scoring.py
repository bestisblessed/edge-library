from pathlib import Path

import pandas as pd

from nfl_trends import rested_after_scoring
from nfl_trends.games import default_games_path, load_games, repo_root

REPO_ROOT = repo_root()


def rested_after_scoring_games():
    return pd.DataFrame(
        [
            {
                "game_id": "2023_01_CHI_DET",
                "season": 2023,
                "week": 1,
                "date": "2023-09-10",
                "home_team": "DET",
                "away_team": "CHI",
                "home_score": 30,
                "away_score": 17,
                "total_line": 44.5,
                "home_rest": 7,
                "away_rest": 7,
                "roof": "dome",
                "environment": "indoor",
            },
            {
                "game_id": "2023_02_DET_GB",
                "season": 2023,
                "week": 2,
                "date": "2023-09-20",
                "home_team": "GB",
                "away_team": "DET",
                "home_score": 20,
                "away_score": 28,
                "total_line": 40.5,
                "home_rest": 7,
                "away_rest": 10,
                "roof": "outdoors",
                "environment": "outdoor",
            },
            {
                "game_id": "2023_03_KC_DET",
                "season": 2023,
                "week": 3,
                "date": "2023-09-28",
                "home_team": "DET",
                "away_team": "KC",
                "home_score": 27,
                "away_score": 24,
                "total_line": 48.0,
                "home_rest": 7,
                "away_rest": 8,
                "roof": "dome",
                "environment": "indoor",
            },
            {
                "game_id": "2024_01_MIN_DET",
                "season": 2024,
                "week": 1,
                "date": "2024-09-08",
                "home_team": "DET",
                "away_team": "MIN",
                "home_score": 27,
                "away_score": 10,
                "total_line": 45.5,
                "home_rest": 7,
                "away_rest": 7,
                "roof": "dome",
                "environment": "indoor",
            },
            {
                "game_id": "2024_02_DET_DAL",
                "season": 2024,
                "week": 2,
                "date": "2024-09-22",
                "home_team": "DAL",
                "away_team": "DET",
                "home_score": 20,
                "away_score": 31,
                "total_line": 47.5,
                "home_rest": 7,
                "away_rest": 14,
                "roof": "closed",
                "environment": "indoor",
            },
            {
                "game_id": "2024_03_GB_DET",
                "season": 2024,
                "week": 3,
                "date": "2024-10-06",
                "home_team": "DET",
                "away_team": "GB",
                "home_score": None,
                "away_score": None,
                "total_line": 51.5,
                "home_rest": 14,
                "away_rest": 7,
                "roof": "dome",
                "environment": "indoor",
            },
        ]
    )


def test_rested_after_scoring_contract():
    result = rested_after_scoring.analyze(rested_after_scoring_games())

    assert result.id == "rested-after-scoring-totals"
    assert result.metadata["holdout_season"] == 2024
    assert result.metadata["team"] == "DET"
    assert result.metadata["claimed_overs"] == 2
    assert result.metadata["claimed_unders"] == 0
    assert result.metadata["live_strategy_rows"] == 1
    assert set(result.audit.loc[result.audit["qualifies"], "game_id"]) == {
        "2023_02_DET_GB",
        "2024_02_DET_DAL",
        "2024_03_GB_DET",
    }
    assert result.summary["games"].sum() == 1
    assert "holdout_summary" in result.secondary
    live = result.secondary["qualifying_games"]
    assert live.loc[live["is_live"], "opponent"].tolist() == ["GB"]


def test_rested_after_scoring_same_season_prior_excludes_week_one_offseason_rest():
    games = rested_after_scoring_games()
    games.loc[games["game_id"].eq("2024_01_MIN_DET"), "home_rest"] = 20

    included = rested_after_scoring.analyze(games)
    allowed = rested_after_scoring.analyze(games, same_season_prior=False)

    assert "2024_01_MIN_DET" not in set(
        included.audit.loc[included.audit["qualifies"], "game_id"]
    )
    assert "2024_01_MIN_DET" in set(
        allowed.audit.loc[allowed.audit["qualifies"], "game_id"]
    )


def test_rested_after_scoring_live_games_are_not_graded_as_pushes():
    result = rested_after_scoring.analyze(rested_after_scoring_games())
    live = result.audit.loc[result.audit["is_live"]]

    assert not live.empty
    assert live["total_result"].isna().all()
    assert int(result.secondary["claimed_window"].iloc[0]["pushes"]) == 0


def test_lions_claimed_window_matches_killersports_14_0():
    games = load_games(default_games_path(REPO_ROOT), require_scores=False)
    result = rested_after_scoring.analyze(games)
    live_ids = result.secondary["qualifying_games"].loc[
        result.secondary["qualifying_games"]["is_live"], "game_id"
    ]

    assert result.metadata["claimed_overs"] == 14
    assert result.metadata["claimed_unders"] == 0
    assert result.metadata["claimed_pushes"] == 0
    assert "2026_07_GB_DET" in set(live_ids)


def test_trend_reads_only_edge_library_data():
    source = Path(rested_after_scoring.__file__).read_text(encoding="utf-8")
    assert "Scrapers/" not in source
    assert "~/Code/nfl-ai" not in source
