# edge-library agent notes

## Data source

`data/` is the single source every current and future trend script reads from.
Do not point new scripts at Twin's nfl-ai tree or at any other copy.

Refresh it from the repo root (Twin's Mac, about weekly):

```bash
cd ~/Code/edge-library && ./update_data.sh
```

`update_data.sh` copies `~/Code/nfl-ai/Scrapers/data/` into `data/` and
`~/Code/nfl-ai/Scrapers/final_data_pfr/` into `data/final_data_pfr/`.

## Layout

- `Main.ipynb` — trend notebook
- `scripts/` — trend scripts; they read CSVs under `data/`
- `nfl_trends/` — parameterized trend audits (read `data/games.csv` only)
- `trends/` — per-trend README, qualifying-games CSV, and chart
- `sbbreakers/` — SBBreakers dictionary notes (not scraper data)
