"""Season filters must not keep the default calendar cut."""

import unittest

import pandas as pd

from scripts.cowboys_after_big_under import (
    DEFAULT_START_DATE as COWBOYS_START_DATE,
)
from scripts.cowboys_after_big_under import analyze as analyze_cowboys
from scripts.cowboys_after_big_under import parse_args as parse_cowboys_args
from scripts.cowboys_after_big_under import start_date_from_args as cowboys_start_date
from scripts.eagles_home_underdog import (
    DEFAULT_START_DATE as EAGLES_START_DATE,
)
from scripts.eagles_home_underdog import analyze as analyze_eagles
from scripts.eagles_home_underdog import parse_args as parse_eagles_args
from scripts.eagles_home_underdog import start_date_from_args as eagles_start_date


def _game(**overrides) -> dict:
    row = {
        "game_id": "g",
        "season": 2020,
        "week": 1,
        "game_type": "REG",
        "date": "2020-09-13",
        "home_team": "PHI",
        "away_team": "NYG",
        "home_score": 24,
        "away_score": 17,
        "spread_line": -3.0,
        "total_line": 44.0,
    }
    row.update(overrides)
    return row


def _qualifying_ids(result) -> set[str]:
    qualifiers = result.audit.loc[result.audit["qualifies"]]
    return set(qualifiers["game_id"])


class SeasonWindowTests(unittest.TestCase):
    def test_eagles_start_season_drops_default_date(self) -> None:
        games = pd.DataFrame(
            [
                _game(
                    game_id="phi-2019",
                    season=2019,
                    date="2019-12-15",
                ),
                _game(game_id="phi-2020", season=2020, date="2020-09-13"),
                _game(
                    game_id="phi-2021",
                    season=2021,
                    date="2021-09-12",
                    home_score=10,
                    away_score=20,
                ),
            ]
        )

        season_only = analyze_eagles(games, start_season=2020)
        self.assertIsNone(season_only.metadata["start_date"])
        self.assertEqual(_qualifying_ids(season_only), {"phi-2020", "phi-2021"})

        cli_args = parse_eagles_args(["--start-season", "2020"])
        from_cli = analyze_eagles(
            games,
            start_season=cli_args.start_season,
            start_date=eagles_start_date(cli_args),
        )
        self.assertEqual(_qualifying_ids(from_cli), {"phi-2020", "phi-2021"})

        explicit = analyze_eagles(
            games,
            start_season=2020,
            start_date=EAGLES_START_DATE,
        )
        self.assertEqual(_qualifying_ids(explicit), {"phi-2021"})

        default = analyze_eagles(games)
        self.assertEqual(default.metadata["start_date"], EAGLES_START_DATE)
        self.assertEqual(_qualifying_ids(default), {"phi-2021"})

    def test_cowboys_start_season_drops_default_date(self) -> None:
        games = pd.DataFrame(
            [
                _game(
                    game_id="dal-under",
                    date="2020-09-13",
                    home_team="DAL",
                    away_team="NYG",
                    home_score=10,
                    away_score=7,
                    total_line=40.0,
                    spread_line=3.0,
                ),
                _game(
                    game_id="dal-2020",
                    date="2020-09-20",
                    week=2,
                    home_team="DAL",
                    away_team="PHI",
                    home_score=24,
                    away_score=20,
                    total_line=44.0,
                    spread_line=-1.0,
                ),
                _game(
                    game_id="dal-pre-dec",
                    season=2021,
                    date="2021-11-14",
                    home_team="DAL",
                    away_team="ATL",
                    home_score=10,
                    away_score=3,
                    total_line=48.0,
                    spread_line=-6.0,
                ),
                _game(
                    game_id="dal-2021",
                    season=2021,
                    date="2021-12-05",
                    home_team="DAL",
                    away_team="NO",
                    home_score=27,
                    away_score=17,
                    total_line=45.0,
                    spread_line=-3.5,
                ),
            ]
        )

        season_only = analyze_cowboys(games, start_season=2020)
        self.assertIsNone(season_only.metadata["start_date"])
        self.assertEqual(_qualifying_ids(season_only), {"dal-2020", "dal-2021"})

        cli_args = parse_cowboys_args(["--start-season", "2020"])
        from_cli = analyze_cowboys(
            games,
            start_season=cli_args.start_season,
            start_date=cowboys_start_date(cli_args),
        )
        self.assertEqual(_qualifying_ids(from_cli), {"dal-2020", "dal-2021"})

        explicit = analyze_cowboys(
            games,
            start_season=2020,
            start_date=COWBOYS_START_DATE,
        )
        self.assertEqual(_qualifying_ids(explicit), {"dal-2021"})

        default = analyze_cowboys(games)
        self.assertEqual(default.metadata["start_date"], COWBOYS_START_DATE)
        self.assertEqual(_qualifying_ids(default), {"dal-2021"})


if __name__ == "__main__":
    unittest.main()
