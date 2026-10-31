"""Notebook summaries must count the same qualifiers as the headline."""

import sys
import unittest
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import cowboys_after_big_under as cowboys
import eagles_division_underdog as division
import eagles_home_underdog as home
import lions_extra_rest_after_scoring as lions


def _side_matches_headline(result) -> None:
    row = result.summary.iloc[0]
    meta = result.metadata
    assert "wins" not in result.summary.columns
    assert int(row.games) == meta["graded_strategy_rows"]
    assert int(row.su_wins) == meta["claimed_su_wins"]
    assert int(row.su_losses) == meta["claimed_su_losses"]
    assert int(row.su_ties) == meta["claimed_su_ties"]
    assert int(row.ats_wins) == meta["claimed_ats_wins"]
    assert int(row.ats_losses) == meta["claimed_ats_losses"]
    assert int(row.ats_pushes) == meta["claimed_ats_pushes"]


class NotebookSummaryTests(unittest.TestCase):
    def test_lions_summary_keeps_the_holdout_season(self):
        games = pd.DataFrame(
            [
                {
                    "game_id": "2024_14_DET_GB",
                    "season": 2024,
                    "date": "2024-12-01",
                    "home_team": "DET",
                    "away_team": "GB",
                    "home_score": 30,
                    "away_score": 10,
                    "total_line": 40,
                    "home_rest": 7,
                    "away_rest": 7,
                },
                {
                    "game_id": "2024_15_GB_DET",
                    "season": 2024,
                    "date": "2024-12-15",
                    "home_team": "GB",
                    "away_team": "DET",
                    "home_score": 20,
                    "away_score": 28,
                    "total_line": 40,
                    "home_rest": 7,
                    "away_rest": 14,
                },
                {
                    "game_id": "2025_14_DET_CHI",
                    "season": 2025,
                    "date": "2025-12-01",
                    "home_team": "DET",
                    "away_team": "CHI",
                    "home_score": 31,
                    "away_score": 10,
                    "total_line": 40,
                    "home_rest": 7,
                    "away_rest": 7,
                },
                {
                    "game_id": "2025_15_CHI_DET",
                    "season": 2025,
                    "date": "2025-12-15",
                    "home_team": "CHI",
                    "away_team": "DET",
                    "home_score": 21,
                    "away_score": 27,
                    "total_line": 40,
                    "home_rest": 7,
                    "away_rest": 14,
                },
            ]
        )
        result = lions.analyze(games, team="DET", start_date="2020-12-01")
        row = result.summary.iloc[0]
        self.assertEqual(result.metadata["claimed_overs"], 2)
        self.assertEqual(int(row.games), 2)
        self.assertEqual(int(row.wins), 2)
        self.assertEqual(int(row.pushes), 0)
        self.assertNotIn("sample", result.summary.columns)

        lions.select_seasons(result, [2024])
        held_out = result.summary.iloc[0]
        self.assertEqual(int(held_out.games), 1)
        self.assertEqual(result.metadata["claimed_overs"], 1)

    def test_home_summary_separates_su_and_ats_across_seasons(self):
        games = pd.DataFrame(
            [
                {
                    "game_id": "2024_05_PHI_NYG",
                    "season": 2024,
                    "date": "2024-10-06",
                    "home_team": "PHI",
                    "away_team": "NYG",
                    "home_score": 17,
                    "away_score": 20,
                    "spread_line": -7,
                },
                {
                    "game_id": "2025_05_PHI_DAL",
                    "season": 2025,
                    "date": "2025-10-05",
                    "home_team": "PHI",
                    "away_team": "DAL",
                    "home_score": 17,
                    "away_score": 20,
                    "spread_line": -7,
                },
            ]
        )
        result = home.analyze(games, team="PHI", start_date="2021-01-01")
        _side_matches_headline(result)
        row = result.summary.iloc[0]
        self.assertEqual(int(row.games), 2)
        self.assertEqual(int(row.su_wins), 0)
        self.assertEqual(int(row.su_losses), 2)
        self.assertEqual(int(row.ats_wins), 2)
        self.assertEqual(int(row.ats_losses), 0)

    def test_snapshot_summaries_match_headlines(self):
        lions_games = lions.load_games(lions.default_games_path(), require_scores=False)
        lions_result = lions.analyze(lions_games)
        lions_row = lions_result.summary.iloc[0]
        meta = lions_result.metadata
        graded = meta["claimed_overs"] + meta["claimed_unders"] + meta["claimed_pushes"]
        self.assertEqual(int(lions_row.games), graded)
        self.assertEqual(int(lions_row.wins), meta["claimed_overs"])
        self.assertGreater(graded, 0)

        side_games = home.load_games(
            home.default_games_path(),
            minimum_season=home.SITUATIONAL_MINIMUM_SEASON,
            require_scores=False,
        )
        for module in (home, division, cowboys):
            result = module.analyze(side_games)
            _side_matches_headline(result)
            seasons = sorted(result.audit["season"].dropna().astype(int).unique())
            module.select_seasons(result, seasons)
            _side_matches_headline(result)


if __name__ == "__main__":
    unittest.main()
