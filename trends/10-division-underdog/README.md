# 10 — Division Underdog

Audit of the KillerSports / SportsBook Breakers claim posted 26 Oct 2026:

> It has been several years since the Eagles have been as large of a dog as
> they are tonight vs an NFC East opponent, getting 4.5 points vs the Cowboys.
> The Eagles are 0-11 ATS since 2016 as a 2+ point dog vs NFC East foes.

## Definitions

| Input | Default | Rule |
|---|---|---|
| Team | `PHI` | nflverse abbreviation |
| Start season | `2016` | NFL season inclusive |
| Min dog points | `2` | `dog_points >= 2`; pick'em excluded |
| Site | `both` | `home`, `road`, or `both` |
| Playoffs | included | `--regular-season-only` to drop them |

Dog points are `-spread_line` when the team is at home and `spread_line` when
the team is on the road. Divisions use the current 32-team map (NFC East:
DAL, NYG, PHI, WAS).

## How to run

From the edge-library repo root:

```bash
python3 -m nfl_trends.division_underdog
python3 scripts/10_division_underdog.py
python3 -m nfl_trends.division_underdog --team DAL --min-dog-points 3 --site road
```

Writes:

- `trends/10-division-underdog/qualifying_games.csv`
- `trends/10-division-underdog/figures/ats-margin.png`

Reads only `data/games.csv`.

## Results on current repository data

Data: Twin's committed `data/` on edge-library main `d0f3074` ("Refresh NFL data").

Philadelphia as a 2+ point NFC East dog since 2016 is **1-10 SU, 2-9 ATS**
(n=11 graded), plus **2 live** games: 2026-10-26 vs DAL (home +4.5) and
2026-11-01 at WAS (road +3.5). Neither live game is final in the file.

That **does not match** the published 0-11 ATS. It does match nfl-ai PR #112.
nflverse closing lines differ from the KillerSports screenshot on both
inclusion and grading:

| Game | nflverse | KillerSports screenshot | Effect |
|---|---|---|---|
| 2016 W14 vs WAS | PHI +1.5, 22-27 | +2.5 | They include a 2+ dog; we do not |
| 2019 W16 vs DAL | PHI +2.0, 17-9 **W / cover** | omitted | We include the only SU/ATS win |
| 2020 W17 vs WAS | PHI +6.5, 14-20, ATS **cover by 0.5** | listed as 2020 W3 +5.5, ATS loss | Same 14-20 score; their 5.5 loses ATS, our 6.5 covers |

Tonight's home spread **-4.5** matches the tweet. The last time Philadelphia
was a division dog this large or larger was **2022-01-08 vs DAL, +6.5**
(`2021_18_DAL_PHI`).

| Variant | SU | ATS | Live |
|---|---|---|---:|
| Primary: 2+ point division dog, 2016+ | 1-10 | 2-9 | 2 |
| 1+ point | 1-11 | 2-10 | 2 |
| 3+ point | 0-10 | 1-9 | 2 |
| Home only, 2+ | 1-3 | 2-2 | 1 |
| Road only, 2+ | 0-7 | 0-7 | 1 |
| Regular season only | 1-10 | 2-9 | 2 |

League-wide 2+ point division dogs since 2016: **281-617-6 SU, 464-421-19 ATS**
(9 live).

Source file: `data/games.csv`.
