# 11 — After Under

Audit of the KillerSports / SportsBook Breakers claim posted 26 Oct 2026:

> The Cowboys are 6-0 ATS (& 6-0 overall) since December 2021 after last game
> went UNDER by 10+ points. Dallas has won by 19.8 ppg and covered by 14.8 ppg.
> Last week's Cowboys/Packers game went under by 18.5 points.

## Definitions

| Input | Default | Rule |
|---|---|---|
| Team | `DAL` | nflverse abbreviation |
| Start date | `2021-12-01` | Game date on or after this day |
| Min under margin | `10` | Prior `total_line - actual_total >= 10` |
| Same-season prior | `true` | Previous game must be in the same NFL season |
| Playoffs | included | `--regular-season-only` to drop current-game playoffs |

`--allow-cross-season-prior` counts week-1 games off a previous-season under.

## How to run

From the edge-library repo root:

```bash
python3 -m nfl_trends.after_under
python3 scripts/11_after_under.py
python3 -m nfl_trends.after_under --team KC --min-under-margin 7 --allow-cross-season-prior
```

Writes:

- `trends/11-after-under/qualifying_games.csv`
- `trends/11-after-under/figures/ats-margin.png`

Reads only `data/games.csv`.

## Results on current repository data

Data: Twin's committed `data/` on edge-library main `d0f3074` ("Refresh NFL data").

Dallas **6-1 SU, 6-1 ATS** (n=7 graded) plus **1 live** qualifier
(`2026_07_DAL_PHI`). Mean win margin **15.714...** (110/7), mean cover
**12.286...** (86/7). That **does not match** the published 6-0 / 19.8 / 14.8.
It does match nfl-ai PR #112 (which reported those means as 15.7 / 12.3).

The extra game is **2022-10-16 at PHI**. The prior contest (2022-10-09 at LAR)
went under by **exactly 10.0** (32 vs a 42.0 total). Dropping only that game
leaves 6-0 with average win margin **19.83** and cover **14.75**, which is the
published 19.8 / 14.8. KillerSports likely had a slightly shorter total on
that Rams game (a 41.5 would be an under of 9.5 and would exclude it) while
still counting 2024-10-06 at PIT, whose prior under is also exactly 10.0 on
nflverse (35 vs 45.0).

Last week: DAL 13 at GB 23 on 2026-10-18, combined **36** vs closing total
**53.5**, under by **17.5**, not 18.5. Tonight still qualifies (17.5 >= 10)
as a live row with home spread -4.5. It is not final in the file.

| Variant | SU | ATS | Live |
|---|---|---|---:|
| Primary: >=10 under, same-season, Dec 2021+ | 6-1 | 6-1 | 1 |
| Under by 7+ | 8-3 | 8-3 | 1 |
| Under by 14+ | 4-0 | 4-0 | 1 |
| Strictly more than 10 (drops both exact-10 priors) | 5-0 | 5-0 | 1 |
| No date cut | 24-22 | 23-22-1 | 1 |
| Cross-season prior allowed | 7-2 | 7-2 | 1 |

League-wide on the primary filter: **265-244-1 SU, 257-238-15 ATS** (10 live).
Dallas is hotter than the baseline, but the exact 6-0 sample is not what
nflverse closing totals produce.

Source file: `data/games.csv`.
