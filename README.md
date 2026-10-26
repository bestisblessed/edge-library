# edge-library

Master notebook and scripts for NFL trend work. Every current and future trend
script reads from `data/`.

## Refresh `data/`

About weekly, on Twin's Mac:

```bash
cd ~/Code/edge-library && ./update_data.sh
```

That replaces `data/` with `~/Code/nfl-ai/Scrapers/data/` and
`~/Code/nfl-ai/Scrapers/final_data_pfr/`. Commit the snapshot when you want it
saved.

## Layout

- `Main.ipynb` — NFL Edge Dictionary notebook
- `scripts/` — trend scripts (read `data/`)
- `nfl_trends/` — parameterized trend audits (read `data/games.csv`)
- `trends/` — per-trend README, qualifying-games CSV, and chart
- `data/` — committed snapshot of nfl-ai scraper masters
- `sbbreakers/` — SBBreakers trend dictionary notes
- `update_data.sh` — local refresh from `~/Code/nfl-ai`
