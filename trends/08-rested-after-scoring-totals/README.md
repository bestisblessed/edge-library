# 08 — Rested After Scoring Totals

Audit of the KillerSports situational claim:

> Lions games are 14-0 to the OVER since December 2020 with more than
> normal rest after scoring at least 24 points last game.

Context for the live qualifier: Detroit is coming off a bye after scoring
45 at Arizona, then hosting Green Bay on 2026-10-25 (`2026_07_GB_DET`).

## Definitions

| Input | Default | Rule |
|---|---|---|
| Team | `DET` | nflverse abbreviation |
| Start date | `2020-12-01` | Game date on or after this day |
| More than normal rest | `rest_days >= 8` | nflverse `home_rest` / `away_rest`; normal Sunday-to-Sunday rest is 7 |
| Prior points | `>= 24` | That team's points in its previous game |
| Same-season prior | `true` | Previous game must be in the same NFL season |
| Result | OVER / UNDER / PUSH | `actual_total - total_line` |

Playoffs are included. Preseason rows are not in `data/games.csv`.

**Why same-season prior games?** Bye weeks and Thursday/Monday extra rest
are intra-season effects. Offseason gaps are a different phenomenon, and
nflverse typically codes week-1 rest as 7, so the cross-season variant
does not change the Detroit list in this window.

**Bye-only** is reported as `rest_days >= 13`, not 14. Recent Lions byes
after a Monday night game are 13 days (Sunday-to-Sunday bye is 14).

## How to run

From the edge-library repo root:

```bash
python3 -m nfl_trends.rested_after_scoring
python3 scripts/08_rested_after_scoring.py
python3 -m nfl_trends.rested_after_scoring --team KC --min-rest-days 10
```

The module writes:

- `trends/08-rested-after-scoring-totals/qualifying_games.csv`
- `trends/08-rested-after-scoring-totals/figures/combined-points-vs-total.png`

Reads only `data/games.csv` (relative to the repo root).

## Results on current repository data

Data: nfl-ai main `ea0ce2810fc9f10f7cc7e3f3912807316102f218` (committed 2026-10-26T05:09:03Z), copied into `data/games.csv`.

Detroit **14-0-0** to the over in the claimed window (n=14 graded), plus **1 live**
qualifier (GB, 2026-10-25, total 53.5, rest 14, prior 45 vs ARI). Scores for
that game are not in the file, so it is not graded.

That matches the published 14-0 claim and the nfl-ai PR #107 record.

| Variant | Graded record | Live |
|---|---|---|
| Primary: rest >= 8, 24+ prior, same-season, Dec 2020+ | 14-0-0 | 1 |
| Rest >= 10 | 10-0-0 | 1 |
| Bye-only (rest >= 13) | 4-0-0 | 1 |
| Rest >= 14 | 0-0-0 | 1 |
| Cross-season prior allowed | 14-0-0 | 1 |
| From 2020-01-01 (drop the December cut) | 14-1-0 | 1 |

League-wide on the same primary filter the over is 156-160-4 (n=320). Detroit is
the outlier, not a league-wide extra-rest scoring effect.

Published claim: [SportsBook Breakers quoting KillerSports](https://x.com/SBBreakers/status/2114383482868658651), 2026-10-25.

Source file: `data/games.csv`. Closing totals, rest days, dates, and scores are
all present for the graded window; no additional scrape was required.
