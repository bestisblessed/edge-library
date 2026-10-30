#!/usr/bin/env python3
"""Denver's rematches after losing the previous meeting by 10+ points.

Uses completed regular-season and playoff games from data/games.csv. The
previous meeting can be in any earlier season; the January 2022 cutoff and
season filter apply to the rematch, not the prior game. Spread lines follow
the dataset convention: positive values favor the home team.
"""
from pathlib import Path
import argparse

import pandas as pd

CUTOFF = '2022-01-01'
DATA = Path(__file__).resolve().parents[1] / 'data' / 'games.csv'


def analyze(path=DATA, seasons=None):
    games = pd.read_csv(path, parse_dates=['date'])
    games = games[(games.game_type != 'PRE') &
                  ((games.home_team == 'DEN') | (games.away_team == 'DEN')) &
                  games.home_score.notna() & games.away_score.notna()].copy()
    games = games.sort_values(['date', 'game_id'])
    home = games.home_team.eq('DEN')
    games['opponent'] = games.away_team.where(home, games.home_team)
    games['margin'] = (games.home_score - games.away_score).where(home, games.away_score - games.home_score)
    games['ats_margin'] = (games.home_score - games.away_score - games.spread_line).where(
        home, games.away_score - games.home_score + games.spread_line)
    grouped = games.groupby('opponent', sort=False)
    for column in ('date', 'game_id', 'margin'):
        games['previous_' + column] = grouped[column].shift()
    games = games[(games.date >= CUTOFF) & (games.previous_margin <= -10)].copy()
    if seasons is not None:
        games = games[games.season.isin(seasons)].copy()
    games['su'] = games.margin.map(lambda x: 'W' if x > 0 else 'L' if x < 0 else 'T')
    games['ats'] = games.ats_margin.map(lambda x: 'N/A' if pd.isna(x) else 'W' if x > 0 else 'L' if x < 0 else 'P')
    return games


def summarize(games):
    def row(label, subset):
        su, ats = subset.su, subset.ats
        return {'Season': label, 'Games': len(subset),
                'SU': f"{sum(su == 'W')}-{sum(su == 'L')}-{sum(su == 'T')}",
                'ATS': f"{sum(ats == 'W')}-{sum(ats == 'L')}-{sum(ats == 'P')}",
                'Missing spread': sum(ats == 'N/A')}
    rows = [row(str(season), group) for season, group in games.groupby('season')]
    rows.append(row('Combined', games))
    return pd.DataFrame(rows)


def details(games):
    result = games[['season', 'date', 'opponent', 'game_id', 'previous_date',
                    'previous_game_id', 'previous_margin', 'margin', 'su', 'ats_margin', 'ats']].copy()
    result['date'] = result.date.dt.strftime('%Y-%m-%d')
    result['previous_date'] = result.previous_date.dt.strftime('%Y-%m-%d')
    result.columns = ['Season', 'Date', 'Opponent', 'Game ID', 'Previous date',
                      'Previous game ID', 'Previous margin', 'Denver margin', 'SU', 'ATS margin', 'ATS']
    return result.reset_index(drop=True)


def show_notebook(games):
    from IPython.display import display
    import matplotlib.pyplot as plt

    display(summarize(games))
    display(details(games))
    if not games.empty:
        counts = games.groupby('season').ats.value_counts().unstack(fill_value=0).reindex(
            columns=['W', 'L', 'P', 'N/A'], fill_value=0)
        counts.plot.bar(stacked=True, color=['#35689a', '#d58b2b', '#aab5bf', '#777777'],
                        xlabel='Season', ylabel='Games', title='Denver ATS results after a 10+ point loss')
        plt.legend(title='ATS result')
        plt.tight_layout()
        plt.show()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', type=Path, default=DATA)
    parser.add_argument('--seasons', type=int, nargs='+', help='Rematch seasons to include')
    parser.add_argument('--notebook', action='store_true', help='Display notebook tables and inline chart')
    args = parser.parse_args()
    games = analyze(args.data, args.seasons)
    if args.notebook:
        show_notebook(games)
    else:
        print(summarize(games).to_string(index=False))
        print('\n' + details(games).to_string(index=False))


if __name__ == '__main__':
    main()
