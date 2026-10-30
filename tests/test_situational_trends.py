from pathlib import Path

import pandas as pd

from conftest import load_script

home_underdog = load_script("09_home_underdog")
division_underdog = load_script("10_division_underdog")
after_under = load_script("11_after_under")
default_games_path = home_underdog.default_games_path
load_games = home_underdog.load_games
repo_root = home_underdog.repo_root
expand_team_games = home_underdog.expand_team_games


REPO = repo_root()


def home_underdog_games():
    return pd.DataFrame(
        [
            {
                "game_id": "2020_14_NO_PHI",
                "season": 2020,
                "week": 14,
                "game_type": "REG",
                "date": "2020-12-13",
                "home_team": "PHI",
                "away_team": "NO",
                "home_score": 24,
                "away_score": 21,
                "spread_line": -7.5,
                "total_line": 49.5,
                "location": "Home",
                "roof": "outdoors",
            },
            {
                "game_id": "2020_17_WAS_PHI",
                "season": 2020,
                "week": 17,
                "game_type": "REG",
                "date": "2021-01-03",
                "home_team": "PHI",
                "away_team": "WAS",
                "home_score": 14,
                "away_score": 20,
                "spread_line": -6.5,
                "total_line": 43.5,
                "location": "Home",
                "roof": "outdoors",
            },
            {
                "game_id": "2021_02_SF_PHI",
                "season": 2021,
                "week": 2,
                "game_type": "REG",
                "date": "2021-09-19",
                "home_team": "PHI",
                "away_team": "SF",
                "home_score": 11,
                "away_score": 17,
                "spread_line": -3.0,
                "total_line": 49.0,
                "location": "Home",
                "roof": "outdoors",
            },
            {
                "game_id": "2021_09_LAC_PHI",
                "season": 2021,
                "week": 9,
                "game_type": "REG",
                "date": "2021-11-07",
                "home_team": "PHI",
                "away_team": "LAC",
                "home_score": 24,
                "away_score": 24,
                "spread_line": 0.0,
                "total_line": 45.0,
                "location": "Home",
                "roof": "outdoors",
            },
            {
                "game_id": "2024_01_NYG_PHI",
                "season": 2024,
                "week": 1,
                "game_type": "REG",
                "date": "2024-09-06",
                "home_team": "PHI",
                "away_team": "NYG",
                "home_score": 28,
                "away_score": 17,
                "spread_line": 5.5,
                "total_line": 43.5,
                "location": "Home",
                "roof": "outdoors",
            },
            {
                "game_id": "2024_20_SB",
                "season": 2024,
                "week": 22,
                "game_type": "SB",
                "date": "2025-02-09",
                "home_team": "PHI",
                "away_team": "KC",
                "home_score": 20,
                "away_score": 27,
                "spread_line": -2.5,
                "total_line": 48.5,
                "location": "Neutral",
                "roof": "closed",
            },
            {
                "game_id": "2026_07_DAL_PHI",
                "season": 2026,
                "week": 7,
                "game_type": "REG",
                "date": "2026-10-26",
                "home_team": "PHI",
                "away_team": "DAL",
                "home_score": None,
                "away_score": None,
                "spread_line": -4.5,
                "total_line": 44.5,
                "location": "Home",
                "roof": "outdoors",
            },
        ]
    )


def division_underdog_games():
    return pd.DataFrame(
        [
            {
                "game_id": "2016_08_PHI_DAL",
                "season": 2016,
                "week": 8,
                "game_type": "REG",
                "date": "2016-10-30",
                "home_team": "DAL",
                "away_team": "PHI",
                "home_score": 29,
                "away_score": 23,
                "spread_line": 5.0,
                "total_line": 44.0,
                "location": "Home",
                "roof": "closed",
            },
            {
                "game_id": "2016_14_WAS_PHI",
                "season": 2016,
                "week": 14,
                "game_type": "REG",
                "date": "2016-12-11",
                "home_team": "PHI",
                "away_team": "WAS",
                "home_score": 22,
                "away_score": 27,
                "spread_line": -1.5,
                "total_line": 48.0,
                "location": "Home",
                "roof": "outdoors",
            },
            {
                "game_id": "2019_16_DAL_PHI",
                "season": 2019,
                "week": 16,
                "game_type": "REG",
                "date": "2019-12-22",
                "home_team": "PHI",
                "away_team": "DAL",
                "home_score": 17,
                "away_score": 9,
                "spread_line": -2.0,
                "total_line": 46.5,
                "location": "Home",
                "roof": "outdoors",
            },
            {
                "game_id": "2021_03_PHI_SF",
                "season": 2021,
                "week": 3,
                "game_type": "REG",
                "date": "2021-09-26",
                "home_team": "SF",
                "away_team": "PHI",
                "home_score": 17,
                "away_score": 11,
                "spread_line": 3.0,
                "total_line": 49.0,
                "location": "Home",
                "roof": "outdoors",
            },
            {
                "game_id": "2026_07_DAL_PHI",
                "season": 2026,
                "week": 7,
                "game_type": "REG",
                "date": "2026-10-26",
                "home_team": "PHI",
                "away_team": "DAL",
                "home_score": None,
                "away_score": None,
                "spread_line": -4.5,
                "total_line": 44.5,
                "location": "Home",
                "roof": "outdoors",
            },
        ]
    )


def after_under_games():
    return pd.DataFrame(
        [
            {
                "game_id": "2021_15_DAL_NYG",
                "season": 2021,
                "week": 15,
                "game_type": "REG",
                "date": "2021-12-19",
                "home_team": "DAL",
                "away_team": "NYG",
                "home_score": 21,
                "away_score": 6,
                "spread_line": 10.0,
                "total_line": 43.0,
                "location": "Home",
                "roof": "closed",
            },
            {
                "game_id": "2021_16_WAS_DAL",
                "season": 2021,
                "week": 16,
                "game_type": "REG",
                "date": "2021-12-26",
                "home_team": "DAL",
                "away_team": "WAS",
                "home_score": 56,
                "away_score": 14,
                "spread_line": 10.5,
                "total_line": 46.0,
                "location": "Home",
                "roof": "closed",
            },
            {
                "game_id": "2022_18_DAL_SF",
                "season": 2021,
                "week": 18,
                "game_type": "WC",
                "date": "2022-01-16",
                "home_team": "DAL",
                "away_team": "SF",
                "home_score": 17,
                "away_score": 23,
                "spread_line": 3.0,
                "total_line": 51.0,
                "location": "Home",
                "roof": "closed",
            },
            {
                "game_id": "2022_01_TB_DAL",
                "season": 2022,
                "week": 1,
                "game_type": "REG",
                "date": "2022-09-11",
                "home_team": "DAL",
                "away_team": "TB",
                "home_score": 3,
                "away_score": 19,
                "spread_line": -2.5,
                "total_line": 49.5,
                "location": "Home",
                "roof": "closed",
            },
            {
                "game_id": "2022_05_DAL_LAR",
                "season": 2022,
                "week": 5,
                "game_type": "REG",
                "date": "2022-10-09",
                "home_team": "LAR",
                "away_team": "DAL",
                "home_score": 10,
                "away_score": 22,
                "spread_line": 5.5,
                "total_line": 42.0,
                "location": "Home",
                "roof": "dome",
            },
            {
                "game_id": "2022_06_DAL_PHI",
                "season": 2022,
                "week": 6,
                "game_type": "REG",
                "date": "2022-10-16",
                "home_team": "PHI",
                "away_team": "DAL",
                "home_score": 26,
                "away_score": 17,
                "spread_line": 6.5,
                "total_line": 42.5,
                "location": "Home",
                "roof": "outdoors",
            },
            {
                "game_id": "2026_06_DAL_GB",
                "season": 2026,
                "week": 6,
                "game_type": "REG",
                "date": "2026-10-18",
                "home_team": "GB",
                "away_team": "DAL",
                "home_score": 23,
                "away_score": 13,
                "spread_line": -1.5,
                "total_line": 53.5,
                "location": "Home",
                "roof": "outdoors",
            },
            {
                "game_id": "2026_07_DAL_PHI",
                "season": 2026,
                "week": 7,
                "game_type": "REG",
                "date": "2026-10-26",
                "home_team": "PHI",
                "away_team": "DAL",
                "home_score": None,
                "away_score": None,
                "spread_line": -4.5,
                "total_line": 44.5,
                "location": "Home",
                "roof": "outdoors",
            },
        ]
    )


def test_spread_sign_convention_positive_means_home_favorite():
    games = expand_team_games(home_underdog_games())
    home_dog = games.loc[games["game_id"].eq("2020_17_WAS_PHI") & games["is_home"]].iloc[0]
    home_fav = games.loc[games["game_id"].eq("2024_01_NYG_PHI") & games["is_home"]].iloc[0]
    pickem = games.loc[games["game_id"].eq("2021_09_LAC_PHI") & games["is_home"]].iloc[0]

    assert home_dog["spread_line"] < 0
    assert home_dog["is_dog"]
    assert home_dog["dog_points"] == 6.5
    assert home_fav["spread_line"] > 0
    assert not home_fav["is_dog"]
    assert pickem["is_pickem"]
    assert not pickem["is_dog"]


def test_home_underdog_contract_and_pickem_exclusion():
    result = home_underdog.analyze(home_underdog_games())

    assert result.id == "home-underdog"
    assert result.metadata["team"] == "PHI"
    assert result.metadata["claimed_su_wins"] == 0
    assert result.metadata["claimed_su_losses"] == 2
    assert result.metadata["claimed_ats_wins"] == 1
    assert result.metadata["claimed_ats_losses"] == 1
    assert result.metadata["live_strategy_rows"] == 1
    assert "2021_09_LAC_PHI" not in set(
        result.audit.loc[result.audit["qualifies"], "game_id"]
    )
    assert "2024_20_SB" not in set(result.audit.loc[result.audit["qualifies"], "game_id"])
    assert "2020_14_NO_PHI" not in set(
        result.audit.loc[result.audit["qualifies"], "game_id"]
    )
    assert "holdout_summary" in result.secondary
    live = result.audit.loc[result.audit["is_live"]]
    assert live["ats_result"].isna().all()
    assert live["su_result"].isna().all()


def test_home_underdog_season_cuts_differ_from_calendar_cut():
    games = home_underdog_games()
    calendar = home_underdog.analyze(games, start_date="2021-01-01", start_season=None)
    season_2020 = home_underdog.analyze(games, start_date=None, start_season=2020)
    season_2021 = home_underdog.analyze(games, start_date=None, start_season=2021)

    assert "2020_14_NO_PHI" in set(
        season_2020.audit.loc[season_2020.audit["qualifies"], "game_id"]
    )
    assert "2020_14_NO_PHI" not in set(
        calendar.audit.loc[calendar.audit["qualifies"], "game_id"]
    )
    assert "2020_17_WAS_PHI" not in set(
        season_2021.audit.loc[season_2021.audit["qualifies"], "game_id"]
    )
    assert "2020_17_WAS_PHI" in set(
        calendar.audit.loc[calendar.audit["qualifies"], "game_id"]
    )


def test_division_underdog_requires_two_plus_points_and_division():
    result = division_underdog.analyze(division_underdog_games())
    qualified = set(result.audit.loc[result.audit["qualifies"], "game_id"])

    assert result.id == "division-underdog"
    assert qualified == {
        "2016_08_PHI_DAL",
        "2019_16_DAL_PHI",
        "2026_07_DAL_PHI",
    }
    assert result.metadata["claimed_su_wins"] == 1
    assert result.metadata["claimed_su_losses"] == 1
    assert result.metadata["claimed_ats_wins"] == 1
    assert result.metadata["claimed_ats_losses"] == 1
    assert result.metadata["live_strategy_rows"] == 1
    one_point = division_underdog.analyze(division_underdog_games(), min_dog_points=1)
    assert "2016_14_WAS_PHI" in set(
        one_point.audit.loc[one_point.audit["qualifies"], "game_id"]
    )


def test_division_underdog_site_filter():
    home = division_underdog.analyze(division_underdog_games(), site="home")
    road = division_underdog.analyze(division_underdog_games(), site="road")

    assert set(home.audit.loc[home.audit["qualifies"], "game_id"]) == {
        "2019_16_DAL_PHI",
        "2026_07_DAL_PHI",
    }
    assert set(road.audit.loc[road.audit["qualifies"], "game_id"]) == {"2016_08_PHI_DAL"}


def test_after_under_same_season_prior_and_live_not_pushed():
    result = after_under.analyze(after_under_games())
    qualified = set(result.audit.loc[result.audit["qualifies"], "game_id"])

    assert result.id == "after-under"
    assert "2021_16_WAS_DAL" in qualified
    assert "2022_06_DAL_PHI" in qualified
    assert "2022_01_TB_DAL" not in qualified
    assert "2026_07_DAL_PHI" in qualified
    live = result.audit.loc[result.audit["is_live"]]
    assert live["ats_result"].isna().all()
    assert int(result.secondary["claimed_window"].iloc[0]["ats_pushes"]) == 0

    allowed = after_under.analyze(after_under_games(), same_season_prior=False)
    assert "2022_01_TB_DAL" in set(
        allowed.audit.loc[allowed.audit["qualifies"], "game_id"]
    )


def test_eagles_home_dog_calendar_cut_matches_0_9_su_2_7_ats():
    games = load_games(
        default_games_path(REPO), minimum_season=2010, require_scores=False
    )
    result = home_underdog.analyze(games)
    live_ids = set(
        result.secondary["qualifying_games"].loc[
            result.secondary["qualifying_games"]["is_live"], "game_id"
        ]
    )
    tonight = result.secondary["qualifying_games"].loc[
        result.secondary["qualifying_games"]["game_id"].eq("2026_07_DAL_PHI")
    ]

    assert result.metadata["claimed_su_wins"] == 0
    assert result.metadata["claimed_su_losses"] == 9
    assert result.metadata["claimed_ats_wins"] == 2
    assert result.metadata["claimed_ats_losses"] == 7
    assert result.metadata["claimed_ats_pushes"] == 0
    assert "2026_07_DAL_PHI" in live_ids
    assert float(tonight.iloc[0]["home_spread"]) == -4.5


def test_eagles_division_dogs_do_not_match_0_11_on_nflverse_lines():
    games = load_games(
        default_games_path(REPO), minimum_season=2010, require_scores=False
    )
    result = division_underdog.analyze(games)
    live_ids = set(
        result.secondary["qualifying_games"].loc[
            result.secondary["qualifying_games"]["is_live"], "game_id"
        ]
    )

    assert result.metadata["claimed_su_wins"] == 1
    assert result.metadata["claimed_su_losses"] == 10
    assert result.metadata["claimed_ats_wins"] == 2
    assert result.metadata["claimed_ats_losses"] == 9
    assert "2026_07_DAL_PHI" in live_ids
    assert result.metadata["last_large_dog_game_id"] == "2021_18_DAL_PHI"
    assert result.metadata["last_large_dog_points"] == 6.5


def test_cowboys_after_under_is_6_1_not_6_0_on_nflverse_totals():
    games = load_games(
        default_games_path(REPO), minimum_season=2010, require_scores=False
    )
    result = after_under.analyze(games)

    assert result.metadata["claimed_su_wins"] == 6
    assert result.metadata["claimed_su_losses"] == 1
    assert result.metadata["claimed_ats_wins"] == 6
    assert result.metadata["claimed_ats_losses"] == 1
    assert result.metadata["tonight_qualifies"]
    assert "2026_07_DAL_PHI" in result.metadata["tonight_game_ids"]
    assert result.metadata["last_game_id"] == "2026_06_DAL_GB"
    assert result.metadata["last_game_under_margin"] == 17.5
    assert result.metadata["tonight_prior_under_margin"] == 17.5


def test_situational_modules_read_only_edge_library_data():
    for module in (home_underdog, division_underdog, after_under):
        source = Path(module.__file__).read_text(encoding="utf-8")
        assert "Scrapers/" not in source
        assert "~/Code/nfl-ai" not in source
