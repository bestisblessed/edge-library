# edge-library

Master notebook and scripts for NFL trend work. Every current and future trend
script reads from `data/`.

## Refresh `data/`

About weekly, on Twin's Mac:

```bash
cd ~/Code/edge-library && ./update_data.sh
```

That replaces `data/` with `~/Code/nfl-ai/Scrapers/data/`. Commit the snapshot
when you want it saved.

## Layout

- `Main.ipynb` — NFL Edge Dictionary notebook
- `scripts/` — trend scripts (read `data/`)
- `data/` — committed snapshot of nfl-ai scraper masters
- `sbbreakers/` — SBBreakers trend dictionary notes
- `update_data.sh` — local refresh from `~/Code/nfl-ai`
