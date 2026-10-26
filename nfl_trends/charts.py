from __future__ import annotations

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

from nfl_trends.models import EdgeResult

BLUE = "#1f4e79"
GOLD = "#c69214"
INK = "#252525"
GRID = "#d9dde3"
OVER = "#2e7d32"
UNDER = "#c62828"
COVER = "#2e7d32"
NO_COVER = "#c62828"
PUSH = "#6b7280"
LIVE = "#7b1fa2"


def _style(axis) -> None:
    axis.spines[["top", "right"]].set_visible(False)
    axis.grid(axis="y", color=GRID, linewidth=0.8, alpha=0.8)
    axis.set_axisbelow(True)
    axis.tick_params(axis="x", labelrotation=25)


def _rested_after_scoring_chart(result: EdgeResult) -> Figure:
    games = result.audit.loc[result.audit["qualifies"]].copy()
    games = games.sort_values(["date", "game_id"]).reset_index(drop=True)
    figure, axis = plt.subplots(figsize=(12, 6))
    if games.empty:
        axis.set_title("No qualifying games")
        axis.set_xlabel("Game")
        axis.set_ylabel("Points")
        _style(axis)
        figure.tight_layout()
        return figure

    labels = []
    for row in games.itertuples(index=False):
        date_value = pd.Timestamp(row.date).strftime("%Y-%m-%d")
        side = "vs" if bool(row.is_home) else "@"
        suffix = " LIVE" if bool(row.is_live) else ""
        labels.append(f"{date_value}\n{side} {row.opponent}{suffix}")
    x = np.arange(len(games))
    result_colors = {"over": OVER, "under": UNDER, "push": PUSH}

    for index, row in games.iterrows():
        total_line = row["total_line"]
        actual = row["actual_total"]
        if pd.notna(total_line) and pd.notna(actual):
            axis.plot(
                [index, index],
                [total_line, actual],
                color=GRID,
                linewidth=1.6,
                zorder=1,
            )
            axis.scatter(
                [index],
                [actual],
                color=result_colors.get(row["total_result"], INK),
                s=70,
                zorder=3,
                edgecolors="white",
                linewidths=0.6,
            )
            axis.scatter(
                [index],
                [total_line],
                color=GOLD,
                marker="s",
                s=36,
                zorder=2,
            )
        elif pd.notna(total_line):
            axis.scatter(
                [index],
                [total_line],
                color=LIVE,
                marker="D",
                s=70,
                zorder=3,
                facecolors="white",
                edgecolors=LIVE,
                linewidths=1.6,
            )

    overs = int(result.metadata.get("claimed_overs", 0))
    unders = int(result.metadata.get("claimed_unders", 0))
    pushes = int(result.metadata.get("claimed_pushes", 0))
    team = result.metadata.get("team", "")
    axis.scatter([], [], color=OVER, s=70, label="Combined points (over)")
    axis.scatter([], [], color=UNDER, s=70, label="Combined points (under)")
    axis.scatter([], [], color=GOLD, marker="s", s=36, label="Closing total")
    axis.scatter(
        [],
        [],
        color=LIVE,
        marker="D",
        s=70,
        facecolors="white",
        edgecolors=LIVE,
        label="Live qualifier (unscored)",
    )
    axis.set_xticks(x, labels)
    axis.set_xlabel("Qualifying game")
    axis.set_ylabel("Points")
    axis.set_title(
        f"{team} extra rest after 24+ previous game: {overs}-{unders}-{pushes} to the over"
    )
    axis.set_ylim(bottom=0)
    axis.legend(frameon=False, loc="upper left")
    _style(axis)
    axis.tick_params(axis="x", labelrotation=0, labelsize=7)
    figure.tight_layout()
    return figure


def _qualifying_ats_margin_chart(result: EdgeResult) -> Figure:
    games = result.audit.loc[result.audit["qualifies"]].copy()
    games = games.sort_values(["date", "game_id"]).reset_index(drop=True)
    figure, axis = plt.subplots(figsize=(12, 6))
    team = result.metadata.get("team", "")
    su = (
        f"{result.metadata.get('claimed_su_wins', 0)}-"
        f"{result.metadata.get('claimed_su_losses', 0)}"
    )
    ats = (
        f"{result.metadata.get('claimed_ats_wins', 0)}-"
        f"{result.metadata.get('claimed_ats_losses', 0)}"
    )
    title = f"{team}: {su} SU, {ats} ATS"
    if games.empty:
        axis.set_title(title)
        axis.set_xlabel("Qualifying game")
        axis.set_ylabel("ATS margin (team)")
        _style(axis)
        figure.tight_layout()
        return figure

    labels = []
    for row in games.itertuples(index=False):
        date_value = pd.Timestamp(row.date).strftime("%Y-%m-%d")
        side = "vs" if bool(row.is_home) else "@"
        suffix = " LIVE" if bool(row.is_live) else ""
        labels.append(f"{date_value}\n{side} {row.opponent}{suffix}")
    x = np.arange(len(games))
    colors = []
    heights = []
    for _, row in games.iterrows():
        if bool(row["is_live"]) or pd.isna(row["team_ats_margin"]):
            colors.append(LIVE)
            heights.append(0.0)
        elif row["ats_result"] == "cover":
            colors.append(COVER)
            heights.append(float(row["team_ats_margin"]))
        elif row["ats_result"] == "push":
            colors.append(PUSH)
            heights.append(float(row["team_ats_margin"]))
        else:
            colors.append(NO_COVER)
            heights.append(float(row["team_ats_margin"]))
    axis.bar(x, heights, color=colors, width=0.72, zorder=2)
    axis.axhline(0, color=INK, linewidth=1, zorder=1)
    axis.scatter(
        x[games["is_live"].fillna(False).to_numpy()],
        [0.0] * int(games["is_live"].fillna(False).sum()),
        color=LIVE,
        marker="D",
        s=70,
        zorder=3,
        facecolors="white",
        edgecolors=LIVE,
        linewidths=1.6,
    )
    axis.set_xticks(x, labels)
    axis.set_xlabel("Qualifying game")
    axis.set_ylabel("ATS margin (team)")
    axis.set_title(title)
    axis.legend(
        handles=[
            Patch(facecolor=COVER, label="ATS win"),
            Patch(facecolor=NO_COVER, label="ATS loss"),
            Patch(facecolor=PUSH, label="Push"),
            Line2D(
                [0],
                [0],
                marker="D",
                color="white",
                markerfacecolor="white",
                markeredgecolor=LIVE,
                markersize=8,
                linestyle="None",
                label="Live qualifier",
            ),
        ],
        frameon=False,
        loc="best",
    )
    _style(axis)
    axis.tick_params(axis="x", labelrotation=0, labelsize=7)
    figure.tight_layout()
    return figure


def chart_for_result(result: EdgeResult) -> Figure:
    if result.id == "rested-after-scoring-totals":
        return _rested_after_scoring_chart(result)
    if result.id in {"home-underdog", "division-underdog", "after-under"}:
        return _qualifying_ats_margin_chart(result)
    raise ValueError(f"No chart contract for edge: {result.id}")
