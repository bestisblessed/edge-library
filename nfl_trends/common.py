from __future__ import annotations

import math

import pandas as pd

from nfl_trends.games import latest_season_split
from nfl_trends.metrics import summarize_binary_market


def metadata_for(frame: pd.DataFrame, source_rows: int) -> dict:
    development, holdout, holdout_season = latest_season_split(frame)
    return {
        "source_rows": int(source_rows),
        "included_rows": int(len(frame)),
        "excluded_rows": int(source_rows - len(frame)),
        "season_start": int(frame["season"].min()),
        "season_end": int(frame["season"].max()),
        "development_rows": int(len(development)),
        "holdout_season": holdout_season,
        "holdout_rows": int(len(holdout)),
    }


def split_research_frame(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return development rows and the latest-season temporal holdout."""
    development, holdout, _ = latest_season_split(frame)
    return development.copy(), holdout.copy()


def market_summary(
    frame: pd.DataFrame,
    group_columns: list[str],
    result_column: str,
    win_label: str,
    value_columns: tuple[str, ...] = (),
) -> pd.DataFrame:
    rows = []
    grouper = group_columns[0] if len(group_columns) == 1 else group_columns
    for key, group in frame.groupby(grouper, observed=True, dropna=False):
        keys = (key,) if len(group_columns) == 1 else key
        row = dict(zip(group_columns, keys))
        row.update(summarize_binary_market(group[result_column], win_label=win_label))
        for column in value_columns:
            row[f"avg_{column}"] = float(group[column].mean())
        rows.append(row)
    return pd.DataFrame(rows)


def descriptive_summary(
    frame: pd.DataFrame, group_columns: list[str], value_columns: tuple[str, ...]
) -> pd.DataFrame:
    rows = []
    grouper = group_columns[0] if len(group_columns) == 1 else group_columns
    for key, group in frame.groupby(grouper, observed=True, dropna=False):
        keys = (key,) if len(group_columns) == 1 else key
        row = dict(zip(group_columns, keys))
        row["games"] = int(len(group))
        for column in value_columns:
            row[f"avg_{column}"] = float(group[column].mean())
        rows.append(row)
    return pd.DataFrame(rows)


def safe_ratio(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator else math.nan
