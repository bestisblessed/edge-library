#!/usr/bin/env python3
"""Analyze how Detroit Lions opponents perform in their next game.

The script reads the NFL game-level CSV, prints the analysis directly to the
terminal, and displays its charts in a Matplotlib window without writing
output files.

By convention in this dataset, ``spread_line`` is positive when the home team
is favored and negative when the away team is favored. Therefore:

    home ATS margin = (home score - away score) - spread_line

Examples:
    python scripts/opponent_stats_after_DET.py
    python scripts/opponent_stats_after_DET.py --seasons 2022 2023 2024 2025 2026
    python scripts/opponent_stats_after_DET.py --data /path/to/games.csv
"""

from __future__ import annotations

import argparse
import csv
import html
import math
from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterable, Sequence

import matplotlib.pyplot as plt


TEAM = "DET"
NON_GAME_TYPES = {"PRE"}
EPSILON = 1e-9


@dataclass(frozen=True)
class Game:
    game_id: str
    season: int
    week: int
    game_type: str
    played_on: date
    away_team: str
    away_score: float
    home_team: str
    home_score: float
    spread_line: float

    def contains(self, team: str) -> bool:
        return team in (self.away_team, self.home_team)

    def opponent_of(self, team: str) -> str:
        if team == self.home_team:
            return self.away_team
        if team == self.away_team:
            return self.home_team
        raise ValueError(f"{team} did not play in {self.game_id}")

    def team_score(self, team: str) -> float:
        return self.home_score if team == self.home_team else self.away_score

    def opponent_score(self, team: str) -> float:
        return self.away_score if team == self.home_team else self.home_score

    def team_margin(self, team: str) -> float:
        return self.team_score(team) - self.opponent_score(team)

    def team_ats_margin(self, team: str) -> float:
        home_ats_margin = (self.home_score - self.away_score) - self.spread_line
        return home_ats_margin if team == self.home_team else -home_ats_margin

    def venue_for(self, team: str) -> str:
        return "home" if team == self.home_team else "away"


@dataclass(frozen=True)
class PostLionsRow:
    season: int
    lions_game: Game
    opponent: str
    next_game: Game

    @property
    def su_margin(self) -> float:
        return self.next_game.team_margin(self.opponent)

    @property
    def ats_margin(self) -> float:
        return self.next_game.team_ats_margin(self.opponent)


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data",
        type=Path,
        default=repo_root / "data" / "games.csv",
        help="Game-level CSV (default: %(default)s)",
    )
    parser.add_argument(
        "--seasons",
        type=int,
        nargs="+",
        default=[2022, 2023, 2024, 2025, 2026],
        help="NFL seasons to analyze (default: 2022 2023 2024 2025 2026)",
    )
    return parser.parse_args()


def require_float(row: dict[str, str], field: str) -> float:
    value = row.get(field, "").strip()
    if not value:
        raise ValueError(f"missing {field}")
    return float(value)


def load_games(path: Path, seasons: set[int]) -> list[Game]:
    required = {
        "game_id", "season", "week", "game_type", "date", "away_team",
        "away_score", "home_team", "home_score", "spread_line",
    }
    games: list[Game] = []
    skipped_incomplete = 0

    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        missing = required.difference(reader.fieldnames or [])
        if missing:
            raise ValueError(f"{path} is missing required columns: {sorted(missing)}")

        for row_number, row in enumerate(reader, start=2):
            try:
                season = int(row["season"])
            except (TypeError, ValueError):
                continue
            if season not in seasons or row["game_type"].strip() in NON_GAME_TYPES:
                continue
            if not row.get("away_score", "").strip() or not row.get("home_score", "").strip():
                skipped_incomplete += 1
                continue
            try:
                games.append(
                    Game(
                        game_id=row["game_id"].strip(),
                        season=season,
                        week=int(row["week"]),
                        game_type=row["game_type"].strip(),
                        played_on=date.fromisoformat(row["date"].strip()),
                        away_team=row["away_team"].strip(),
                        away_score=require_float(row, "away_score"),
                        home_team=row["home_team"].strip(),
                        home_score=require_float(row, "home_score"),
                        spread_line=require_float(row, "spread_line"),
                    )
                )
            except ValueError as exc:
                raise ValueError(f"invalid completed row {row_number} in {path}: {exc}") from exc

    if not games:
        raise ValueError(f"no completed non-preseason games found for {sorted(seasons)}")
    ids = [game.game_id for game in games]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate game_id values found in selected completed games")
    if skipped_incomplete:
        print(f"Note: skipped {skipped_incomplete} incomplete/unlined selected-season rows.")
    return sorted(games, key=lambda game: (game.played_on, game.game_id))


def analyze(games: Sequence[Game], seasons: Sequence[int]) -> tuple[list[Game], list[PostLionsRow]]:
    games_by_team_season: dict[tuple[int, str], list[Game]] = defaultdict(list)
    for game in games:
        games_by_team_season[(game.season, game.away_team)].append(game)
        games_by_team_season[(game.season, game.home_team)].append(game)

    lions_games = [game for game in games if game.contains(TEAM)]
    rows: list[PostLionsRow] = []
    for lions_game in lions_games:
        opponent = lions_game.opponent_of(TEAM)
        next_games = [
            game
            for game in games_by_team_season[(lions_game.season, opponent)]
            if game.played_on > lions_game.played_on
        ]
        if next_games:
            rows.append(
                PostLionsRow(
                    season=lions_game.season,
                    lions_game=lions_game,
                    opponent=opponent,
                    next_game=min(next_games, key=lambda game: (game.played_on, game.game_id)),
                )
            )

    if not lions_games:
        raise ValueError(f"no completed Lions games found for seasons {sorted(seasons)}")
    return lions_games, rows


def outcome(margin: float, push_label: str = "T") -> str:
    if margin > EPSILON:
        return "W"
    if margin < -EPSILON:
        return "L"
    return push_label


def record(margins: Iterable[float], push_label: str = "T") -> tuple[int, int, int, str]:
    values = list(margins)
    wins = sum(value > EPSILON for value in values)
    losses = sum(value < -EPSILON for value in values)
    pushes = len(values) - wins - losses
    return wins, losses, pushes, f"{wins}-{losses}-{pushes}" if pushes else f"{wins}-{losses}"


def win_rate(margins: Iterable[float]) -> float:
    values = list(margins)
    decisions = sum(abs(value) > EPSILON for value in values)
    return sum(value > EPSILON for value in values) / decisions if decisions else math.nan


def format_score(value: float) -> str:
    return str(int(value)) if value.is_integer() else f"{value:g}"


def format_line_for_team(game: Game, team: str) -> str:
    team_line = -game.spread_line if team == game.home_team else game.spread_line
    return f"{team_line:+g}"


def write_detail_csv(path: Path, rows: Sequence[PostLionsRow]) -> None:
    fields = [
        "season", "lions_week", "lions_game_type", "lions_date", "lions_game_id",
        "opponent", "next_game_week", "next_game_type", "next_game_date",
        "days_after_lions", "next_game_id", "next_game_venue", "next_game_against",
        "opponent_score", "other_team_score", "opponent_line", "su_margin",
        "su_result", "ats_margin", "ats_result",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            game = row.next_game
            writer.writerow(
                {
                    "season": row.season,
                    "lions_week": row.lions_game.week,
                    "lions_game_type": row.lions_game.game_type,
                    "lions_date": row.lions_game.played_on.isoformat(),
                    "lions_game_id": row.lions_game.game_id,
                    "opponent": row.opponent,
                    "next_game_week": game.week,
                    "next_game_type": game.game_type,
                    "next_game_date": game.played_on.isoformat(),
                    "days_after_lions": (game.played_on - row.lions_game.played_on).days,
                    "next_game_id": game.game_id,
                    "next_game_venue": game.venue_for(row.opponent),
                    "next_game_against": game.opponent_of(row.opponent),
                    "opponent_score": format_score(game.team_score(row.opponent)),
                    "other_team_score": format_score(game.opponent_score(row.opponent)),
                    "opponent_line": format_line_for_team(game, row.opponent),
                    "su_margin": f"{row.su_margin:g}",
                    "su_result": outcome(row.su_margin),
                    "ats_margin": f"{row.ats_margin:g}",
                    "ats_result": outcome(row.ats_margin, "P"),
                }
            )


def summaries(
    seasons: Sequence[int], lions_games: Sequence[Game], rows: Sequence[PostLionsRow]
) -> list[dict[str, str]]:
    output: list[dict[str, str]] = []
    for season in seasons:
        season_lions = [game for game in lions_games if game.season == season]
        season_rows = [row for row in rows if row.season == season]
        lions_su = record(game.team_margin(TEAM) for game in season_lions)[3]
        lions_ats = record((game.team_ats_margin(TEAM) for game in season_lions), "P")[3]
        post_su = record(row.su_margin for row in season_rows)[3]
        post_ats = record((row.ats_margin for row in season_rows), "P")[3]
        ats_rate = win_rate(row.ats_margin for row in season_rows)
        fade_rate = win_rate(-row.ats_margin for row in season_rows)
        output.append(
            {
                "season": str(season),
                "lions_games": str(len(season_lions)),
                "lions_su": lions_su,
                "lions_ats": lions_ats,
                "post_lions_games": str(len(season_rows)),
                "opponents_next_game_su": post_su,
                "opponents_next_game_ats": post_ats,
                "opponents_ats_win_rate_ex_pushes": f"{ats_rate:.1%}",
                "fade_opponents_ats_record": record((-row.ats_margin for row in season_rows), "P")[3],
                "fade_ats_win_rate_ex_pushes": f"{fade_rate:.1%}",
            }
        )
    if len(seasons) > 1:
        all_ats_rate = win_rate(row.ats_margin for row in rows)
        all_fade_rate = win_rate(-row.ats_margin for row in rows)
        output.append(
            {
                "season": "Combined",
                "lions_games": str(len(lions_games)),
                "lions_su": record(game.team_margin(TEAM) for game in lions_games)[3],
                "lions_ats": record((game.team_ats_margin(TEAM) for game in lions_games), "P")[3],
                "post_lions_games": str(len(rows)),
                "opponents_next_game_su": record(row.su_margin for row in rows)[3],
                "opponents_next_game_ats": record((row.ats_margin for row in rows), "P")[3],
                "opponents_ats_win_rate_ex_pushes": f"{all_ats_rate:.1%}",
                "fade_opponents_ats_record": record((-row.ats_margin for row in rows), "P")[3],
                "fade_ats_win_rate_ex_pushes": f"{all_fade_rate:.1%}",
            }
        )
    return output


def write_summary_csv(path: Path, rows: Sequence[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def svg_text(x: float, y: float, text: str, size: int = 16, **attrs: str) -> str:
    extra = " ".join(f'{key.replace("_", "-")}="{html.escape(value)}"' for key, value in attrs.items())
    return f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" {extra}>{html.escape(text)}</text>'


def write_rate_chart(path: Path, summary_rows: Sequence[dict[str, str]]) -> None:
    width, height = 1200, 700
    left, right, top, bottom = 130, 60, 135, 110
    plot_w, plot_h = width - left - right, height - top - bottom
    summary_rows = [row for row in summary_rows if row["season"] != "Combined"]
    seasons = [row["season"] for row in summary_rows]
    su_rates = []
    ats_rates = []
    counts = []
    for row in summary_rows:
        su_w, su_l, *_ = [int(value) for value in row["opponents_next_game_su"].split("-")]
        ats_w, ats_l, *_ = [int(value) for value in row["opponents_next_game_ats"].split("-")]
        su_rates.append(su_w / (su_w + su_l))
        ats_rates.append(ats_w / (ats_w + ats_l))
        counts.append(int(row["post_lions_games"]))

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#fbfaf7"/>',
        svg_text(left, 52, "Lions opponents in their next game", 30, font_family="Arial, sans-serif", font_weight="700", fill="#20262e"),
        svg_text(left, 84, "Straight-up and ATS win rates by NFL season; pushes excluded from rate", 17, font_family="Arial, sans-serif", fill="#5d6670"),
    ]
    for tick in range(0, 101, 20):
        y = top + plot_h * (1 - tick / 100)
        parts.append(f'<line x1="{left}" y1="{y:.1f}" x2="{left + plot_w}" y2="{y:.1f}" stroke="#d9dce0" stroke-width="1"/>')
        parts.append(svg_text(left - 18, y + 6, f"{tick}%", 14, font_family="Arial, sans-serif", text_anchor="end", fill="#5d6670"))
    benchmark_y = top + plot_h * 0.5
    parts.append(f'<line x1="{left}" y1="{benchmark_y:.1f}" x2="{left + plot_w}" y2="{benchmark_y:.1f}" stroke="#30363d" stroke-width="2" stroke-dasharray="8 7"/>')
    parts.append(svg_text(left + plot_w - 4, benchmark_y - 10, "50% reference", 14, font_family="Arial, sans-serif", text_anchor="end", fill="#30363d"))

    group_w = plot_w / len(seasons)
    bar_w = min(120, group_w * 0.27)
    colors = ("#35689a", "#d58b2b")
    for index, season in enumerate(seasons):
        center = left + group_w * (index + 0.5)
        for offset, value, color, label in (
            (-bar_w * 0.58, su_rates[index], colors[0], "SU"),
            (bar_w * 0.58, ats_rates[index], colors[1], "ATS"),
        ):
            x = center + offset - bar_w / 2
            y = top + plot_h * (1 - value)
            h = plot_h * value
            parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w:.1f}" height="{h:.1f}" rx="4" fill="{color}" stroke="#28313a" stroke-width="1"/>')
            parts.append(svg_text(x + bar_w / 2, y - 12, f"{value:.1%}", 18, font_family="Arial, sans-serif", font_weight="700", text_anchor="middle", fill="#20262e"))
            parts.append(svg_text(x + bar_w / 2, top + plot_h + 28, label, 14, font_family="Arial, sans-serif", text_anchor="middle", fill="#5d6670"))
        parts.append(svg_text(center, top + plot_h + 63, season, 20, font_family="Arial, sans-serif", font_weight="700", text_anchor="middle", fill="#20262e"))
        parts.append(svg_text(center, top + plot_h + 88, f"n={counts[index]} post-Lions games", 14, font_family="Arial, sans-serif", text_anchor="middle", fill="#5d6670"))
    parts.append('</svg>')
    path.write_text("\n".join(parts), encoding="utf-8")


def write_cumulative_chart(path: Path, rows: Sequence[PostLionsRow]) -> None:
    width, height = 1200, 760
    left, right, top, bottom = 115, 70, 135, 110
    plot_w, plot_h = width - left - right, height - top - bottom
    rows = sorted(rows, key=lambda row: (row.next_game.played_on, row.next_game.game_id))
    values = []
    total = 0
    for row in rows:
        # A fade wins when the post-Lions opponent fails to cover.
        total += -1 if row.ats_margin > EPSILON else 1 if row.ats_margin < -EPSILON else 0
        values.append(total)
    y_min = min(0, min(values)) - 1
    y_max = max(0, max(values)) + 1

    def x_pos(index: int) -> float:
        return left + (plot_w * index / max(1, len(values) - 1))

    def y_pos(value: float) -> float:
        return top + plot_h * (y_max - value) / (y_max - y_min)

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#fbfaf7"/>',
        svg_text(left, 52, "Cumulative ATS units from fading post-Lions opponents", 30, font_family="Arial, sans-serif", font_weight="700", fill="#20262e"),
        svg_text(left, 84, "One unit per game: win +1, loss -1, push 0; ordered by next-game date", 17, font_family="Arial, sans-serif", fill="#5d6670"),
    ]
    for tick in range(math.ceil(y_min), math.floor(y_max) + 1, 2):
        y = y_pos(tick)
        parts.append(f'<line x1="{left}" y1="{y:.1f}" x2="{left + plot_w}" y2="{y:.1f}" stroke="#d9dce0" stroke-width="1"/>')
        parts.append(svg_text(left - 18, y + 6, f"{tick:+d}", 14, font_family="Arial, sans-serif", text_anchor="end", fill="#5d6670"))
    zero_y = y_pos(0)
    parts.append(f'<line x1="{left}" y1="{zero_y:.1f}" x2="{left + plot_w}" y2="{zero_y:.1f}" stroke="#30363d" stroke-width="2"/>')
    points = " ".join(f"{x_pos(i):.1f},{y_pos(value):.1f}" for i, value in enumerate(values))
    parts.append(f'<polyline points="{points}" fill="none" stroke="#35689a" stroke-width="4" stroke-linejoin="round" stroke-linecap="round"/>')
    for index, (row, value) in enumerate(zip(rows, values)):
        color = "#35689a" if row.ats_margin < -EPSILON else "#d58b2b" if row.ats_margin > EPSILON else "#ffffff"
        parts.append(f'<circle cx="{x_pos(index):.1f}" cy="{y_pos(value):.1f}" r="5" fill="{color}" stroke="#28313a" stroke-width="1.5"><title>{html.escape(str(row.season))} {html.escape(row.opponent)}: fade {"W" if row.ats_margin < -EPSILON else "L" if row.ats_margin > EPSILON else "P"}; cumulative {value:+d}</title></circle>')
    for season in sorted(set(row.season for row in rows)):
        indices = [index for index, row in enumerate(rows) if row.season == season]
        center = (indices[0] + indices[-1]) / 2
        parts.append(svg_text(x_pos(center), top + plot_h + 52, str(season), 20, font_family="Arial, sans-serif", font_weight="700", text_anchor="middle", fill="#20262e"))
        if indices[-1] < len(rows) - 1:
            boundary = (x_pos(indices[-1]) + x_pos(indices[-1] + 1)) / 2
            parts.append(f'<line x1="{boundary:.1f}" y1="{top}" x2="{boundary:.1f}" y2="{top + plot_h}" stroke="#8b939b" stroke-width="1.5" stroke-dasharray="5 6"/>')
    parts.append(svg_text(left + plot_w, y_pos(values[-1]) - 12, f"Final: {values[-1]:+d} units", 17, font_family="Arial, sans-serif", font_weight="700", text_anchor="end", fill="#20262e"))
    parts.append('</svg>')
    path.write_text("\n".join(parts), encoding="utf-8")


def print_report(summary_rows: Sequence[dict[str, str]], detail_rows: Sequence[PostLionsRow]) -> None:
    print("\nDetroit Lions / post-Lions opponent analysis")
    print("=" * 82)
    print(f"{'Season':<10}{'DET SU':<12}{'DET ATS':<12}{'Opp next SU':<15}{'Opp next ATS':<16}{'Fade ATS':<12}")
    for row in summary_rows:
        print(
            f"{row['season']:<10}{row['lions_su']:<12}{row['lions_ats']:<12}"
            f"{row['opponents_next_game_su']:<15}{row['opponents_next_game_ats']:<16}"
            f"{row['fade_opponents_ats_record']:<12}"
        )
    print("\nPost-Lions next games")
    print("-" * 82)
    print(f"{'Season':<8}{'After DET':<12}{'Team':<7}{'Next game':<17}{'Score':<10}{'Line':<8}{'SU':<5}{'ATS':<5}")
    for row in sorted(detail_rows, key=lambda item: (item.season, item.lions_game.played_on)):
        game = row.next_game
        matchup = f"{row.opponent} vs {game.opponent_of(row.opponent)}" if game.venue_for(row.opponent) == "home" else f"{row.opponent} @ {game.opponent_of(row.opponent)}"
        score = f"{format_score(game.team_score(row.opponent))}-{format_score(game.opponent_score(row.opponent))}"
        print(
            f"{row.season:<8}{('W' + str(row.lions_game.week)):<12}{row.opponent:<7}{matchup:<17}"
            f"{score:<10}{format_line_for_team(game, row.opponent):<8}"
            f"{outcome(row.su_margin):<5}{outcome(row.ats_margin, 'P'):<5}"
        )


def show_charts(summary_rows: Sequence[dict[str, str]], rows: Sequence[PostLionsRow]) -> None:
    season_rows = [row for row in summary_rows if row["season"] != "Combined"]
    seasons = [row["season"] for row in season_rows]
    su_rates = []
    ats_rates = []
    for row in season_rows:
        su_w, su_l, *_ = map(int, row["opponents_next_game_su"].split("-"))
        ats_w, ats_l, *_ = map(int, row["opponents_next_game_ats"].split("-"))
        su_rates.append(su_w / (su_w + su_l))
        ats_rates.append(ats_w / (ats_w + ats_l))

    ordered_rows = sorted(rows, key=lambda row: (row.next_game.played_on, row.next_game.game_id))
    fade_units = []
    total = 0
    for row in ordered_rows:
        total += 1 if row.ats_margin < -EPSILON else -1 if row.ats_margin > EPSILON else 0
        fade_units.append(total)

    positions = list(range(len(seasons)))
    width = 0.36
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    axes[0].bar([x - width / 2 for x in positions], su_rates, width, label="SU", color="#35689a")
    axes[0].bar([x + width / 2 for x in positions], ats_rates, width, label="ATS", color="#d58b2b")
    axes[0].axhline(0.5, color="black", linestyle="--", linewidth=1)
    axes[0].set(
        title="Post-Lions Win Rates",
        xlabel="Season",
        ylabel="Win rate",
        ylim=(0, 1),
        xticks=positions,
        xticklabels=seasons,
    )
    axes[0].legend()

    axes[1].plot(range(1, len(fade_units) + 1), fade_units, marker="o", color="#35689a")
    axes[1].axhline(0, color="black", linewidth=1)
    axes[1].set(
        title="Cumulative ATS Units Fading Post-Lions Teams",
        xlabel="Post-Lions game",
        ylabel="Units",
    )

    fig.tight_layout()
    plt.show(block=True)


def main() -> int:
    args = parse_args()
    seasons = sorted(set(args.seasons))
    games = load_games(args.data, set(seasons))
    lions_games, detail_rows = analyze(games, seasons)
    available_seasons = sorted(set(game.season for game in lions_games))
    missing_seasons = sorted(set(seasons).difference(available_seasons))
    if missing_seasons:
        print(
            "Note: no completed non-preseason Lions games found for "
            f"season(s): {', '.join(map(str, missing_seasons))}."
        )
    summary_rows = summaries(available_seasons, lions_games, detail_rows)

    print_report(summary_rows, detail_rows)
    show_charts(summary_rows, detail_rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
