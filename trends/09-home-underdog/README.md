# 09 — Home Underdog

Audit of the KillerSports / SportsBook Breakers claim posted 26 Oct 2026:

> The Eagles have not won a game as a home dog since the 2020 season! Since
> then, Philadelphia as a home dog is: 0-9 overall, 2-7 vs the spread. The
> Eagles are home dogs vs the Cowboys on MNF tonight.

## Spread convention

nflverse `spread_line` is the **expected home scoring margin**. Positive means
the home team is favored, negative means the home team is the underdog, and 0
is pick'em.

```text
home_ats_margin = (home_score - away_score) - spread_line
dog_points (home) = -spread_line
```

Tonight (`2026_07_DAL_PHI`, 2026-10-26, DAL at PHI) is in the file as a live
qualifier: `spread_line = -4.5`, so Philadelphia is a **4.5-point home dog**.
Pick'em is excluded. Pushes are graded, not dropped. Neutral-site games are
not home games.

## "Since the 2020 season"

| Reading | Graded SU | Graded ATS | Live | Matches 0-9 / 2-7? |
|---|---|---|---:|---|
| Calendar `2021-01-01` (default) | 0-9 | 2-7 | 1 | Yes |
| 2020 NFL season inclusive | 1-11 | 5-7 | 1 | No |
| 2021 NFL season onward | 0-8 | 1-7 | 1 | No |

The calendar cut includes 2020 week 17 vs WAS (played 3 Jan 2021, PHI +6.5,
14-20, SU loss, ATS cover) and excludes 2020 games played in calendar 2020,
including the 13 Dec 2020 home-dog **win** vs New Orleans. Neither NFL-season
cut reproduces 0-9 SU / 2-7 ATS.

## How to run

From the edge-library repo root:

```bash
python3 -m nfl_trends.home_underdog
python3 scripts/09_home_underdog.py
python3 -m nfl_trends.home_underdog --team NYG --start-season 2021 --min-spread 3
```

Writes:

- `trends/09-home-underdog/qualifying_games.csv`
- `trends/09-home-underdog/figures/ats-margin.png`

Reads only `data/games.csv`.

## Results on current repository data

Data: nfl-ai main `ea0ce2810fc9f10f7cc7e3f3912807316102f218`.

Philadelphia **0-9 SU, 2-7 ATS** (n=9 graded, no pushes) plus **1 live**
qualifier: DAL, 2026-10-26, home spread -4.5. That game is not final in
`data/games.csv`.

Matches the published 0-9 / 2-7 claim and nfl-ai PR #112.

| Variant | SU | ATS | Live |
|---|---|---|---:|
| Primary: calendar 2021-01-01, any home dog | 0-9 | 2-7 | 1 |
| 2020 NFL season inclusive | 1-11 | 5-7 | 1 |
| 2021 NFL season onward | 0-8 | 1-7 | 1 |
| 2010+ home dogs | 6-24 | 11-19 | 1 |
| Min dog 1 point | 0-9 | 2-7 | 1 |
| Min dog 3 points | 0-8 | 2-6 | 1 |
| Regular season only | 0-9 | 2-7 | 1 |

Same window, PHI as a **road** dog: 9-5 SU / 9-5 ATS (plus 1 live). League-wide
home dogs: **201-386-3 SU, 293-282-15 ATS** (8 live).

Source file: `data/games.csv`.
