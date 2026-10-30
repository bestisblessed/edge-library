from pathlib import Path

import pandas as pd
import pytest

from conftest import load_script

games_module = load_script("08_rested_after_scoring")
default_games_path = games_module.default_games_path
latest_season_split = games_module.latest_season_split
load_games = games_module.load_games
repo_root = games_module.repo_root


def write_csv(tmp_path: Path, name: str, rows: list[dict]) -> Path:
    path = tmp_path / name
    pd.DataFrame(rows).to_csv(path, index=False)
    return path


def test_load_games_filters_incomplete_rows_and_normalizes_roof(tmp_path):
    path = write_csv(
        tmp_path,
        "games.csv",
        [
            {
                "game_id": "2024_01_A_B",
                "season": 2024,
                "home_team": "B",
                "away_team": "A",
                "home_score": 24,
                "away_score": 17,
                "roof": "closed",
            },
            {
                "game_id": "2024_02_C_D",
                "season": 2024,
                "home_team": "D",
                "away_team": "C",
                "home_score": None,
                "away_score": None,
                "roof": "outdoors",
            },
        ],
    )

    games = load_games(path)

    assert games["game_id"].tolist() == ["2024_01_A_B"]
    assert games["environment"].tolist() == ["indoor"]


def test_load_games_can_keep_unscored_upcoming_rows(tmp_path):
    path = write_csv(
        tmp_path,
        "games.csv",
        [
            {
                "game_id": "2024_01_A_B",
                "season": 2024,
                "home_team": "B",
                "away_team": "A",
                "home_score": 24,
                "away_score": 17,
                "roof": "closed",
            },
            {
                "game_id": "2024_02_C_D",
                "season": 2024,
                "home_team": "D",
                "away_team": "C",
                "home_score": None,
                "away_score": None,
                "roof": "outdoors",
            },
        ],
    )

    games = load_games(path, require_scores=False)

    assert games["game_id"].tolist() == ["2024_01_A_B", "2024_02_C_D"]


def test_load_games_rejects_missing_required_columns(tmp_path):
    path = write_csv(tmp_path, "games.csv", [{"season": 2024}])

    with pytest.raises(ValueError, match="missing required columns"):
        load_games(path)


def test_load_games_applies_minimum_season(tmp_path):
    path = write_csv(
        tmp_path,
        "games.csv",
        [
            {
                "game_id": "2019_01_A_B",
                "season": 2019,
                "home_team": "B",
                "away_team": "A",
                "home_score": 20,
                "away_score": 17,
                "roof": "outdoors",
            },
            {
                "game_id": "2020_01_A_B",
                "season": 2020,
                "home_team": "B",
                "away_team": "A",
                "home_score": 24,
                "away_score": 17,
                "roof": "outdoors",
            },
        ],
    )

    games = load_games(path)

    assert games["game_id"].tolist() == ["2020_01_A_B"]


def test_load_games_rejects_duplicate_game_ids(tmp_path):
    row = {
        "game_id": "2024_01_A_B",
        "season": 2024,
        "home_team": "B",
        "away_team": "A",
        "home_score": 24,
        "away_score": 17,
        "roof": "outdoors",
    }
    path = write_csv(tmp_path, "games.csv", [row, row])

    with pytest.raises(ValueError, match="duplicate"):
        load_games(path)


def test_latest_season_split_uses_maximum_season():
    data = pd.DataFrame({"season": [2022, 2023, 2024, 2024], "value": [1, 2, 3, 4]})

    development, holdout, season = latest_season_split(data)

    assert season == 2024
    assert development["season"].tolist() == [2022, 2023]
    assert holdout["value"].tolist() == [3, 4]


def test_latest_season_split_rejects_empty_frame():
    with pytest.raises(ValueError, match="empty"):
        latest_season_split(pd.DataFrame({"season": []}))


def test_default_games_path_is_data_games_csv():
    path = default_games_path()

    assert path == repo_root() / "data" / "games.csv"
    assert path.exists()


def test_load_games_keeps_unscored_repo_rows_used_by_live_qualifiers():
    games = load_games(default_games_path(), require_scores=False)
    gb = games.loc[games["game_id"].eq("2026_07_GB_DET")].iloc[0]
    phi = games.loc[games["game_id"].eq("2026_07_DAL_PHI")].iloc[0]

    assert pd.isna(gb["home_score"]) and pd.isna(gb["away_score"])
    assert float(gb["total_line"]) == 53.5
    assert pd.isna(phi["home_score"]) and pd.isna(phi["away_score"])
    assert float(phi["spread_line"]) == -4.5


def test_games_loader_does_not_reference_nfl_ai_paths():
    source = Path(games_module.__file__).read_text(encoding="utf-8")
    assert "Scrapers/" not in source
    assert "~/Code/nfl-ai" not in source
